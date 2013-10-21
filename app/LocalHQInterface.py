__author__ = 'Akaash'
import datetime
import MySQLdb
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash

def getBarcodeList(localDB):
    query = "Select barcode from product_information"
    localDB.execute(query)
    result = list(localDB.fetchall())
    return result


def getListOfStaffID(localDB):
    query = "Select staff_Id from cashiers order by staff_Id"
    localDB.execute(query)
    result = list(localDB.fetchall())
    return result

def createNewUser(address,contact,dob,gender,name,t_pass,localDB, hqDB):
    contact = "" + str(contact)
    contact.replace('+','')
    contact.replace('-','')
    if(not(contact.isdigit())):
        return False
    query = "select max(staff_Id) from hq_staff"
    result = hqDB.execute(query)
    index=1;
    if(result):
        index = hqDB.fetchone()[0] + 1
    query = "Insert into hq_staff values(%s,'%s','%s','%s','%s',%s,'%s','%s')" % (str(index), MySQLdb.escape_string(name), MySQLdb.escape_string(address),gender,dob,str(MySQLdb.escape_string(contact)),'Staff','Shops007')
    result = hqDB.execute(query)
    if not result:
        return False
    if str(t_pass).rstrip().__len__()==0:
        t_pass = name.replace(' ','') + str(index)
    query = "Insert into cashiers values(%s,'%s','%s')" %(str(index), MySQLdb.escape_string(name), generate_password_hash(t_pass))
    result = localDB.execute(query)
    if not result:
        return False
    return True

def getListOfStaff(localDB):
    query = "Select staff_Id, name from cashiers order by staff_Id"
    localDB.execute(query)
    return list(localDB.fetchall())

def getListOfTransactions(localDB):
    query = "Select A.transaction_Id,A.date,B.barcode,A.staff_Id,B.price,b.units_sold from transactions A,transactions_info B where A.transaction_Id = B.transaction_Id order by A.date DESC"
    localDB.execute(query)
    return list(localDB.fetchall())

def getListOfProducts(localDB):
    query = "Select barcode,name,category,manufacturer,remaining_quantity,active_price,member_price from product_information"
    localDB.execute(query)
    return list(localDB.fetchall())

def sendemail(id,name,email):
    s=smtplib.SMTP()
    s.connect('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login("cegshop07", "abcde@12")
    header = ""
    header += 'Subject: CEG Shop 07: Request for Password Reset\n\n'
    msg = "\nGreetings! Your new password is : %s%s .\n\nYours sincerely, \nCEG Shop 07"  % (str(name),str(id))
    response = s.sendmail("cegshop07@gmail.com", email, header+msg)
    print response
    s.quit()
    return True

def resetPassword(id,email,localDB):
    query = "select name from managers where staff_Id = %s" % (str(id))
    qresult = localDB.execute(query)
    if(not qresult):
        return False
    result = list(localDB.fetchone())
    encrypted = generate_password_hash(str(result[0]).replace(' ','')+str(id))
    query = "Update managers set `password` ='%s' where staff_Id = %s" % (encrypted, str(id))
    localDB.execute(query)
    name = ""+result[0]
    sendemail((id),name.replace(' ',''),email)

def getStaffPermission(localDB):
    query = "Show grants for 'CG3002'@'localhost'"
    localDB.execute(query)
    result=""
    result_query = localDB.fetchone()
    result += result_query[0]
    if(result.find('ALL PRIVILEGES')== -1):
        return 1
    return 0


def changePassword(id,old,new,localDB):
    oldquery = "select password from managers where staff_Id = %s" % (id)
    localDB.execute(oldquery)
    result = localDB.fetchone()
    if(not check_password_hash(result[0],old)):
        return False
    encrypted = generate_password_hash(MySQLdb.escape_string(new))
    query = "Update managers set `password` ='%s' where staff_Id = %s" % (encrypted, id)
    result = localDB.execute(query)
    if(result):
        return True
    else:
        return False

def lockdownPermission(localDB):
    query = "revoke all privileges, grant option from 'CG3002'@'localhost';"
    localDB.execute(query)
    result = localDB.fetchone()
    return

def releasePermission(localDB):
    query = "grant all privileges on *.* to 'CG3002'@'localhost';"
    localDB.execute(query)
    result = localDB.fetchone()
    return

def getStaffName(staffID, localDB):
    query = "Select name from managers where staff_id = %s" % (MySQLdb.escape_string(staffID))
    result = localDB.execute(query)
    if(result):
        retieve_name = localDB.fetchone()
        return retieve_name[0]
    else:
        #query = "Select name from managers where staff_id = %s " % (MySQLdb.escape_string(staffID))
        #result = localDB.execute(query)
        #if(result):
        #    retieve_name = localDB.fetchone()
        #    return retieve_name[0]
        #else:
        return ""

def checkShopLogin(staffID, epassword, localDB):
    staffID = "" + staffID
    if(not(staffID.isdigit())):
        return False
    query = "Select password from managers where staff_id = %s" % (MySQLdb.escape_string(staffID))
    result = localDB.execute(query)
    if(result):
        retieve_pass_cash = localDB.fetchone()
        return check_password_hash(retieve_pass_cash[0],epassword)
    else:
        #query = "Select password from managers where staff_id = %s " % (MySQLdb.escape_string(staffID))
        #result = localDB.execute(query)
        #if(result):
        #    retieve_pass_manager = localDB.fetchone()
        #    return pwd_context.verify(password,retieve_pass_manager[0])
        #else:
        return False

def clearLocalCashierTable(localDB):
    query = "Delete from cashiers"
    localDB.execute(query)

def populateLocalCashierTable(localDB, hqDB):
    query = "Select staff_Id,name from hq_staff where shop_Id='Shops007' and position='Staff'"
    hqDB.execute(query)
    rows = hqDB.fetchall()
    for row in rows:
        local_query = "Insert into cashiers value ("+MySQLdb.escape_string(str(row[0]))+","+"'"+MySQLdb.escape_string(row[1])+"',"+"'"+generate_password_hash(str(row[1]+str(row[0])).lower().replace(' ',''))+"')"
        localDB.execute(local_query)

def updateLocalManagerTable(localDB, hqDB):
    query2 = "Select staff_Id, name from hq_staff where position LIKE '%Manager%' and shop_Id='Shops007' order by(staff_Id)"
    hqDB.execute(query2)
    result = []
    qresult = list(hqDB.fetchall())
    for row in qresult:
        newrow = [row[0],row[1],'']
        result.append(newrow)
    for row in result:
        newQuery = "Select password from managers where staff_Id='%s'" % row[0]
        result2 =localDB.execute(newQuery)
        if(result2):
            qresult = list(localDB.fetchone())
            row[2] = qresult[0]
        else:
            row[2] = generate_password_hash(str(row[1]).replace(' ','')+str(row[0]))
    newQuery = "Truncate table managers"
    localDB.execute(newQuery)
    for row in result:
        newQuery = "Insert into managers values(%s,'%s','%s');" % (row[0], row[1], row[2])
        localDB.execute(newQuery)


def clearLocalMemberTable(localDB):
    query = "Delete from members"
    localDB.execute(query)
    pass

def populateLocalMemberTable(localDB, hqDB):
    query = "Select phone,name from hq_members"
    hqDB.execute(query)
    rows = hqDB.fetchall()
    for row in rows:
        local_query = "Insert into members value ("+MySQLdb.escape_string(str(row[0]))+","+"'"+MySQLdb.escape_string(row[1])+"')"
        localDB.execute(local_query)

def submitTransactionsToHQ(localDB, hqDB):
    query = "Select  A.transaction_Id, A.barcode, A.price, A.units_sold, B.date from transactions_info A, transactions B where A.transaction_Id=B.transaction_Id;"
    localDB.execute(query)
    rows = list(localDB.fetchall())
    for Transaction in rows:
        Barcode = Transaction[1]
        TotalPrice = 0;
        UnitSold = 0;
        Date = Transaction[4]
        if len(Transaction[0]) > 1:
            for j in range(len(rows)):
                tempTransaction = rows[j]
                if tempTransaction[1] == Barcode and tempTransaction[4] == Date:
                    rows[j] = ""
                    UnitSold += tempTransaction[3]
                    TotalPrice += tempTransaction[2]*tempTransaction[3]
            newQuery = "Insert into hq_transactions values ('Shops007',"+"'"+(Barcode)+"',"+str(TotalPrice)+","+str(UnitSold)+",'"+datetime.date.strftime(Date,"%Y-%m-%d")+"')"
            hqDB.execute(newQuery)


def clearLocalTransactionDatabase(localDB):
    query = "Delete from transactions_info"
    localDB.execute(query)
    query = "Delete from transactions"
    localDB.execute(query)
    pass

def addTransactionToLocal(staff_Id,barcode,quantity, localDB):
    error = '1'
    date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
    print date
    idquery = "select transaction_Id from transactions"
    localDB.execute(idquery)
    lists = (localDB.fetchall())
    print lists
    transaction_Id = 0
    if len(lists) == 0:
        transaction_Id += 1
    else:
        newlist = []
        for row in lists:
            temp = "" + row[0]
            newlist.append(int(temp))
        print newlist.sort()
        transaction_Id = newlist[len(newlist)-1] + 1
    price = []
    for row in range(len(barcode)):
        tempbar = barcode.__getitem__(row)
        query2 = "select active_price from product_information where barcode = '%s' " % str(tempbar)
        result = localDB.execute(query2)
        if(not result):
            return "Barcode in Set " + str(row) + " not found."
        price.append(localDB.fetchone()[0])
    query3 = "Insert into transactions values('%s','%s',%s)" %(str(transaction_Id),date,str(staff_Id))
    result = localDB.execute(query3)
    if(not result):
        return "Addition Failed. Please try again."
    for row in range(len(barcode)):
        query4 = "Insert into transactions_info values('%s', '%s', %s, %s);" %(str(transaction_Id), str(barcode.__getitem__(row)),str(price.__getitem__(row)),str(quantity.__getitem__(row)) )
        result = localDB.execute(query4)
        if(not result):
            return "Addition Failed. Please try again."
    return error

def updateHQShopInventory(localDB, hqDB):
    query = "Select A.barcode, A.remaining_quantity from product_information A"
    localDB.execute(query)
    result = list(localDB.fetchall())
    for row in result:
        newQuery = "Select count(*) from hq_shop_inventories where shop_Id = 'Shops007' and barcode ="+"'"+row[0]+"'"
        result = hqDB.execute(newQuery)
        if(result):
            newQuery = "Update hq_shop_inventories set quantity = %s where barcode = %s" % (str(row[1]),"'"+row[0]+"'")
            hqDB.execute(newQuery)

def clearLocalShopInventory(localDB):
    query = "Delete from product_information"
    localDB.execute(query)


def populateLocalShopInventory(localDB, hqDB):
    query = "Select A.barcode, A.active_price, A.quantity, B.name, B.category, B.manufacturer, B.bundle_unit_qty, B.bundle_unit_discount, B.member_price from hq_shop_inventories A, hq_products B where A.barcode = B.barcode and A.shop_Id = 'Shops007'"
    hqDB.execute(query)
    result = list(hqDB.fetchall())
    for row in result:
        newQuery = "Insert into product_information values("+"'"+row[0]+"',"+"'"+MySQLdb.escape_string(row[3])+"',"+"'"+MySQLdb.escape_string(row[4])+"',"+"'"+MySQLdb.escape_string(row[5])+"',"+str(row[2])+","+str(row[6])+","+str(row[7])+","+str(row[1])+","+str(row[8])+")"
        print newQuery
        localDB.execute(newQuery)

def performEOD(localDB, hqDB):
    submitTransactionsToHQ(localDB,hqDB)
    updateHQShopInventory(localDB,hqDB)


def performSOD(localDB, hqDB):
    clearLocalTransactionDatabase(localDB)
    clearLocalCashierTable(localDB)
    clearLocalMemberTable(localDB)
    clearLocalShopInventory(localDB)
    updateLocalManagerTable(localDB,hqDB)
    populateLocalCashierTable(localDB,hqDB)
    populateLocalMemberTable(localDB,hqDB)
    populateLocalShopInventory(localDB,hqDB)
    return True