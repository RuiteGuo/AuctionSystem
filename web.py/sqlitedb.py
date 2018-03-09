import web

db = web.database(dbn='sqlite',
        db='AuctionBase'
    )

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()
# Sample usage (in auctionbase.py):
#
# t = sqlitedb.transaction()
# try:
#     sqlitedb.query('[FIRST QUERY STATEMENT]')
#     sqlitedb.query('[SECOND QUERY STATEMENT]')
# except Exception as e:
#     t.rollback()
#     print str(e)
# else:
#     t.commit()
#
# check out http://webpy.org/cookbook/transactions for examples

# returns the current time from your database
def getTime():
    # TODO: update the query string to match
    # the correct column and table name in your database
    query_string = 'select Time from CurrentTime'
    results = query(query_string)
    # alternatively: return results[0]['currenttime']
    return results[0].Time
                                  # column name
# returns a single item specified by the Item's ID in the database
# Note: if the `result' list is empty (i.e. there are no items for a
# a given ID), this will throw an Exception!
def getItemById(item_id):
    # TODO: rewrite this method to catch the Exception in case `result' is empty
    query_string = 'select * from Items where ItemID = $ItemIDVar'
    result = query(query_string, {'ItemIDVar': item_id})
    if len(result) > 0:
        return result[0]
    return None

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}):
    return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################
# e.g. to update the current time
def setTime(newTime):
    t = transaction()
    query_string = 'UPDATE CurrentTime SET Time = $newTimeVar'
    try:
        db.query(query_string, {'newTimeVar': newTime})
    except Exception as e:
        t.rollback()
        return False
    else:
        t.commit()
        return True
    return True

def search(searchKeys):
    endingString = []
#    query_string = "SELECT * FROM Items WHERE itemID = $itemID and Seller_UserID = $userID and Currently <= $maxPrice and Currently >= $minPrice "
    query_string = "SELECT * FROM Items WHERE "
    index = 0;
    try:
        for keys in searchKeys:
            if keys != "":
                if index == 0:
                    endingString.append("itemID = " + str(searchKeys[0]))
                if index == 1:
                    endingString.append("Seller_UserID = $userID")
                if index == 2:
                    endingString.append("Currently >= " + str(searchKeys[2]))
                if index == 3:
                    endingString.append("Currently <= " + str(searchKeys[3]))
                if index == 4:
                    endingString.append("Description LIKE $itemDescription")
                if index == 5:
                    if searchKeys[5] == "open":
                        endingString.append("Started <= $time AND Ends > $time AND ((Buy_Price IS NOT NULL AND Currently < Buy_Price) OR Buy_Price IS NULL)")
                    elif searchKeys[5] == "close":
                        endingString.append("(Ends <= $time OR (Buy_Price IS NOT NULL AND Currently >= Buy_Price))")
                    elif searchKeys[5] == "notStarted":
                        endingString.append("Started > $time")
                    else:
                        endingString.append("1 = 1")
            index = index + 1
        ending = " AND ".join(endingString)
        query_string = query_string + ending + ";"
        result = db.query(query_string, {"userID":searchKeys[1], "itemDescription": "%" + searchKeys[4] + "%", "time":getTime()})
    except Exception as e :
        return None
    return result



def getAttributesInfo(attributes, key):
    if (attributes == "Item") :
        #key is item ID
        return getItemById(key)

    if (attributes == "Status"):
        #key is item
        time = getTime()
        # trigger5 is caught
        if key["Started"] > time:
            return ("The bid for this Item Has not started yet")
        # trigger6 is caught
        if key["Ends"] <= time:
            return ("The Bid is currently closed")


        if key["Buy_Price"] != None:
            if float(key["Currently"]) >= float(key["Buy_Price"]):
                return "Current Bid Price has exceeded buy price, Bid Closed"

        return "Open"

    if (attributes == "User"):
        query_3 = 'select * from Users where UserID = $ID'
        result_3 = query(query_3, {'ID': key})
        if len(result_3) > 0:
            return result_3[0]
        else:
            return None

    return None


def addBid (inputArray):
    #inputArray item is organized in following order: itemID, user ID, Price
    t = transaction()
    if ((inputArray[0]=="" or None)or(inputArray[1]=="" or None)or(inputArray[2]=="" or None)):
        return("",False)

    try:
        item = getAttributesInfo("Item",inputArray[0]);
        if item == None:
            raise Exception("Item Not Found for this Item ID")
        user = getAttributesInfo("User",inputArray[1]);
        if user == None or "":
            raise Exception ("User Not Found for this User Id")

        status = getAttributesInfo("Status",item);
        if status != "Open":
            raise Exception(status)


        #catch the exception of trigger3 new amount has to be greater than current amount
        if float(inputArray[2]) <= item["Currently"]:
            message = "Current price for this item is higher than the entered bid price"
            raise Exception (message)

        # trigger 7
        if item["Seller_UserID"] == user:
            raise Exception ("Seller can't bid on the item they sell, you dummy !!!")

        query_string = "INSERT INTO Bids (ItemID, UserID, Amount, Time ) VALUES ($ItemID,$UserID,$Amount,$Time)"
        result = db.query(query_string,{"ItemID": inputArray[0], "UserID": inputArray[1], "Amount": inputArray[2], "Time": getTime()})

    except Exception as e :
        t.rollback()
        return (str(e),False)

    else:
        t.commit();
        return ("", True);

    return

def item(itemID):
    item = getItemById(itemID)
    time = getTime()
    get_bids_query_string = "SELECT * FROM Bids WHERE ItemID = $itemID ORDER BY Amount DESC"
    bids = query(get_bids_query_string,{"itemID": item["ItemID"]})

    get_cats_query_string = "SELECT Category FROM Categories WHERE ItemID = $itemID"
    cats = query(get_cats_query_string,{"itemID": item["ItemID"]})

    status = "Open"
    if item["Started"] > time:
        status = "Not Started"
    if item["Buy_Price"]!=None:
        if item["Currently"] >= item["Buy_Price"]:
            status="Closed"
    if item["Ends"] <= time:
        status = "Closed"

    if len(bids) > 0 and status == "Closed":
        return(status, str(bids[0]["UserID"]), bids, cats)
    return (status,"Nobody has won this item!",bids,cats)
