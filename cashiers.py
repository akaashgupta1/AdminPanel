import ctypes
import datetime

import serial
import os
import MySQLdb
import re
import logging
import sys

ser = serial.Serial()
error_type = {}
error_type['barcode_nf'] = 'E2'
error_type['member_nf'] = 'E3'
error_type['quantity_e'] = 'E4'
error_type['error'] = 'E1'
error_type['undo_impossible'] = 'E5'
response_format = '%s%s@'
pdu_format = '!%s#%s@'
pdu_data_format = '%s/%s'
tempstring = [''] * 50
members = [0] * 50
aggregateprice = [[] for i in range(50)]
cashiertalking = [1] * 50 # for entire instruction toggle
pdulist = [''] * 50
cashiertime = [''] * 50
cashiertransactionid = [''] * 50
firstbarcode = [0] * 50
querystring = [''] * 50
instructiontoggle = [0]*50

def tohex(int_value, limit):
    getBin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)
    result = getBin(int_value, int(limit))
    return (result.strip())


def writePIDToFile(pid):
    f = open('lock.pid', 'r+')
    f.truncate()
    f.write(pid)
    f.close()


def serialInit():
    ser.port = "COM6"
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.STOPBITS = serial.STOPBITS_TWO
    ser.parity = serial.PARITY_NONE
    ser.setTimeout(0)
    ser.open()
    print ser.portstr
    return # open first serial port   # check which port was really used


def readFunc():
    readIn = ser.read()
    if readIn != '':
        sys.stdout.write(readIn)
        pass
    return readIn


def codeInit(code_string, header):
    print "Uploading Code"
    ser.write(chr(header))
    ser.write(chr(header))
    ser.write(chr(header))
    ser.write(code_string)
    print "Upload Complete"
    return


def writeFunc(_in):
    try:
        ser.write(_in)
    except:
        print "Could not write"
    return

def getTransactionID(cursor):
    idquery = "select transaction_Id from transactions"
    cursor.execute(idquery)
    lists = (cursor.fetchall())
    transaction_Id = 0
    if len(lists) == 0:
        transaction_Id += 1
    else:
        newlist = []
        for row in lists:
            temp = "" + row[0]
            newlist.append(int(temp))
        #print newlist.sort()
        newlist.sort()
        transaction_Id = newlist[len(newlist) - 1] + 1
    return transaction_Id


def poplastquery(id):
    global querystring
    query = querystring[id]
    if (len(query) > 0):
        splitted = query.split('!;!')
        splitted.pop()
        querystring[id] = ''.join(splitted)
    return


def processInstruction(id, instr, cursor):
    global cashiertalking, members, tempstring, error_type, aggregateprice, querystring
    result = ''
    if (cashiertalking[int(id)] == 1):
        cashiertime[int(id)] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S');
        cashiertransactionid[int(id)] = getTransactionID(cursor)
    if (instr == '' or len(instr) < 2):
        result = error_type['error']
        return result
    print instr
    # print querystring[int(id)]
    # print aggregateprice[int(id)]

    if (instr[2] == 'M'):
        if (cashiertalking[int(id)] == 1):
            query = 'select count(*) from members where phone_number = %s' % str(instr[3:11])
            cursor.execute(query)
            result = cursor.fetchone()
            if (result[0] != 0):
                members[int(id)] = 1;
                result = 'S'
            else:
                result = error_type['member_nf']
        else:
            print 'yes'
            result = error_type['error']
    elif (instr[2] == 'B'):  #processing barcode
        try:
            barcode = int(instr[3:11])
            quantity = int(instr[11:13])
        except:
            #print '3'
            result = error_type['error']
            return result
        query = 'select active_price, member_price, remaining_quantity,bundle_unit_size,bundle_unit_discount from product_information where barcode = %s' % str(
            barcode)
        result = cursor.execute(query)
        if (not result):
            return error_type['barcode_nf']
        result = cursor.fetchone()
        ap = result[0]
        mp = result[1]
        rq = result[2]
        bus = result[3]
        bud = result[4]
        if (quantity > int(rq)):
            return error_type['quantity_e']
        if (float(ap) >= float(mp) and members[int(id)] == 1):
            return_price = float(mp)
        else:
            return_price = float(ap)
        if (int(bus) != 0):
            if (int(quantity) > int(bus)):
                return_price = ((100 - int(bud)) * return_price) / 100.0
        decimal = return_price
        print decimal
        getBin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)
        binary = getBin(int(decimal), 16)
        binaryq = chr(int(binary[0:8], 2)).__add__(chr(int(binary[8:16], 2)))
        binaryd = chr(int(getBin((int(decimal * 100)) % 100, 8), 2))
        multiply = decimal*quantity
        if (firstbarcode[int(id)] == 0):
            querystring[int(id)] = querystring[int(id)].__add__("insert into transactions values('%s','%s',%s)!;!" % (
                str(cashiertransactionid[int(id)]), cashiertime[int(id)], id))
            firstbarcode[int(id)] = 1
            #query = "select price, units_sold from transactions_info where barcode = '%s' and transaction_Id = '%s'" % (str(barcode),str(cashiertransactionid[int(id)]))
        result = querystring[int(id)].find(str(barcode))
        if (result == -1):
            querystring[int(id)] = querystring[int(id)].__add__(
                "insert into transactions_info values('%s','%s',%s,%s)!;!" % (
                    str(cashiertransactionid[int(id)]), str(barcode), str(float(decimal * quantity)), str(quantity)))
        else:
            upreg = re.compile("update transactions_info set price =.{1,40}where barcode = '%s' and transaction_Id = '%s'!;!" % (
                     str(barcode), str(cashiertransactionid[int(id)])))
            list = upreg.findall(querystring[int(id)])
            if(not list):
                inreg = re.compile("insert into transactions_info values\('%s','%s'.{1,50}\)!;!" % (str(cashiertransactionid[int(id)]), str(barcode)))
                list = inreg.findall(querystring[int(id)])
                if(not list):
                    return error_type['error']
                stringresult = list[0][list[0].find(str(barcode))+10:list[0].find(')!;!')]
                result = stringresult.split(',')
            else:
                locationprice = list[0].find('price')
                locationunits = list[0].find('units_sold')
                result = []
                result.append(list[0][locationprice+8:locationprice+list[0][locationprice:].find(',')])
                result.append(list[0][locationunits+13:locationunits+list[0][locationunits:].find(' where')])
            querystring[int(id)] = querystring[int(id)].__add__(
                "update transactions_info set price = %s, units_sold = %s where barcode = '%s' and transaction_Id = '%s'!;!" % (
                    str(float(result[0]) + decimal * quantity), str(int(result[1]) + quantity), str(barcode),
                    str(cashiertransactionid[int(id)])))
            querystring[int(id)] = querystring[int(id)].__add__(
                "update product_information set remaining_quantity = %s where barcode = '%s'!;!" % (
                    str(int(rq - quantity),str(barcode))))
        result = 'S'.__add__(str(binaryq)).__add__(str(binaryd))
        aggregateprice[int(id)].append(multiply)
    elif (instr[2] == 'U'):
        if (len(aggregateprice[int(id)]) > 0):
            getBin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)
            multiply = (aggregateprice[int(id)][-1])
            listofprice = getBin(int(multiply), 18)
            multiplyq = chr(int(listofprice[2:10], 2)).__add__(chr(int(listofprice[10:18], 2)))
            multiplyd = chr(int(getBin((int(multiply * 100)) % 100, 8), 2))
            result = chr(int(listofprice[0:2].__add__('111100'),2)).__add__(multiplyq.__add__(multiplyd))
            aggregateprice[int(id)].pop()
            poplastquery(int(id))
            if len(aggregateprice[int(id)]) == 0:
                cashiertalking[int(id)] = 1
                firstbarcode[int(id)] = 0
                members[int(id)] = 0
                querystring[int(id)] = ''
            return result
        else:
            print 'hahaha'
            cashiertalking[int(id)] = 1
            members[int(id)] = 0
            firstbarcode[int(id)] = 0
            return error_type['undo_impossible']
    elif (instr[2] == 'N'):         # writing to database - end of transaction
        if (len(querystring[int(id)]) > 0):
            stringofqueries = str(querystring[int(id)].replace('!;!', ';'))
            listofqueries = stringofqueries.split(';')
            for row in listofqueries:
                if row :
                    try:
                        cursor.execute(row)
                    except:
                        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S', filename='Error.log',level=logging.DEBUG)
                        logging.debug('Transaction Failed. Cashier Id = 5s on query = %s',str(int(id)), row)
                        result = error_type['error']
                        return result
        result = 'N' # transaction processed
    elif (instr[2] == 'X'):
        querystring[int(id)] = ''
        result = 'S' # transaction processed
    if (instr[2] == 'N' or instr[2] == 'X'): # end of transaction
        cashiertalking[int(id)] = 1
        members[int(id)] = 0
        cashiertime[int(id)] = ''
        cashiertransactionid[int(id)] = ''
        firstbarcode[int(id)] = 0
        aggregateprice[int(id)][:] = []
        querystring[int(id)] = ''
    elif (cashiertalking[int(id)] == 1):
        cashiertalking[int(id)] = 0
    return result


def process(char, id, db):
    cursor = db.cursor()
    if (char):
        a = tohex(int(id),8)
        if chr(int(('1111'.__add__(a[0:4])), 2)) == char:
            instructiontoggle[int(id)] = 1
        if instructiontoggle[int(id)] == 1:
            tempstring[int(id)] += char
    if (char == '@'):
        instructiontoggle[int(id)] = 0
        #print tempstring[int(id)]
        result = processInstruction(id, tempstring[int(id)], cursor)
        if result == "N":
            db.commit()
            result = 'S'
        tempstring[int(id)] = ''
        a = (tohex(id, 8))
        firstpartheader = chr(int(('1111'.__add__(a[0:4])), 2))
        secondpartheader = chr(int((a[4:8].__add__('1111')), 2))
        writeFunc(response_format % (firstpartheader.__add__(secondpartheader), result))
    return 'continue'


def localdb():
    ldb = MySQLdb.connect(host="127.0.0.1", # your host, usually localhost
                          user='CG3002', # your username
                          passwd='sansar', # your password
                          db='shop_db', # name of the data base
                          port=3306)
    ldb.autocommit(0)
    return ldb


def communicationStart():
    db = localdb()
    initializePDUTable(db.cursor())
    for i in range(1, 50):
        a = (tohex(i, 16))
        b = chr(int((a[0:8]), 2)).__add__(chr(int((a[8:16]), 2)))
        writeFunc(pdu_format % (b, pdulist[i]))
    while True:
        for i in range(1, 50):
            a = (tohex(i, 8))
            firstpartheader = chr(int(('1111'.__add__(a[0:4])), 2))
            secondpartheader = chr(int((a[4:8].__add__('1111')), 2))
            writeFunc(response_format % (firstpartheader.__add__(secondpartheader), ''))
            start = datetime.datetime.now()
            while (datetime.datetime.now() - start).microseconds < 35000:
                value = readFunc()
                process(value, i, db)


def initializePDUTable(cursor):
    global pdulist
    query = 'select A.pdu_index, A.barcode, B.active_price from pdu A, product_information B where A.barcode = B.barcode'
    result = cursor.execute(query)
    if (result):
        result = cursor.fetchall()
        for i in result:
            pi = int(i[0])
            b = str(i[1])
            ap = float(i[2])
            if (pi < 50):
                pdulist[pi] = pdu_data_format % ((b), str(ap))


def CashierFunc():         # uploading the cashier program
    code_path = "C_TIMER.HEX"
    with open(code_path, "r") as codefile:
        code_string = codefile.read()
    codeInit(code_string, 0x23)
    start = datetime.datetime.now()
    while ((datetime.datetime.now() - start).seconds < 1):
        pass
    print 'Cashier Transfer succeeded.'
    return


def PDUFunc():              # uploading the PDU program
    code_path = "P_TIMER.HEX"
    with open(code_path, "r") as codefile:
        code_string = codefile.read()
    codeInit(code_string, 0x26)
    start = datetime.datetime.now()
    while (datetime.datetime.now() - start).seconds < 1:
        pass
    print 'PDU Transfer succeeded.'
    return


def runProg():
    ctypes.windll.kernel32.SetConsoleTitleA("Cashier Interface")
    writePIDToFile(str(os.getpid()))
    while True:
        try:
            serialInit()
            break
        except:
            print('Error occurred in establishing communication with cashiers. Please reboot.')
    CashierFunc()
    ser.flushInput()
    PDUFunc()
    ser.flushInput()
    communicationStart()
    ser.close()
    return


runProg()

#---------------------------------------------------------------------------------------------------------------#


