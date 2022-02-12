import tornado.ioloop
import tornado.web
import tornado.escape
import motor.motor_tornado
import json
import base64

client = motor.motor_tornado.MotorClient("mongodb://localhost:27017/?retryWrites=true&w=majority")
db = client.storage

class ADD(tornado.web.RequestHandler):
    async def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body)
            
            if data:
                key = base64.b64encode(json.dumps(data).encode('utf-8'))
                key = key.decode('ascii')
                select = await self.settings["db"]["storage"].find_one({"_id": key})
                if select is None:

                    data['_id'] = key
                    data['duplicates'] = 1
                    new_item = await self.settings["db"]["storage"].insert_one(data)
                    self.set_status(201)
                    self.write({"id":key})
                else:
                    data['duplicates'] = select['duplicates'] + 1
                    await self.settings["db"]["storage"].update_one({"_id": key}, {"$set": data})
                    self.write({"id":key})
            else:
                self.set_status(400)
                self.write("no data")
        except:
            self.set_status(500)
            self.write("server error")


class GET(tornado.web.RequestHandler):
    async def get(self):
        try:
            key = self.get_argument('key', False)
            if key:
                item = await self.settings["db"]["storage"].find_one({"_id": key})
                if item is not None:
                    item.pop('_id', None)
                    self.write(item)
                else:    
                    self.set_status(404)
                    self.write("no data")
            else:
                self.set_status(400)
                self.write("no key")
        except:
            self.set_status(500)
            self.write("server error")


class PUT(tornado.web.RequestHandler):
    async def put(self):
        try:
            if self.request.body:
                data = tornado.escape.json_decode(self.request.body)
            else:
                data = {}
            if 'id' in data.keys():
                old_key = data['id']
                data.pop('id', None)
                old_data = await self.settings["db"]["storage"].find_one({"_id": old_key})
                await db["storage"].delete_one({"_id": old_key})

                if data is not None:
                    
                    key = base64.b64encode(json.dumps(data).encode('utf-8'))
                    key = key.decode('ascii')

                    data['_id'] = key
                    data['duplicates'] = 1
                    await self.settings["db"]["storage"].insert_one(data)

                    self.set_status(201)
                    self.write({"id":key})
                else:    
                    self.set_status(404)
                    self.write("no data")
            else:
                self.set_status(400)
                self.write("no key")
        except:
            self.set_status(500)
            self.write("server error")


class DELETE(tornado.web.RequestHandler):
    async def delete(self):
        try:
            if self.request.body:
                data = tornado.escape.json_decode(self.request.body)
            else:
                data = {}
            if 'key' in data.keys():
                key = data['key']
                item = await self.settings["db"]["storage"].find_one({"_id": key})
                deleted_item = await db["storage"].delete_one({"_id": key})

                if deleted_item.deleted_count == 1:
                    self.set_status(200)
                    self.write("item deleted")
                else:
                    self.set_status(404)
                    self.write("item not found")
            else:
                self.set_status(400)
                self.write("no key")
        except:
            self.set_status(500)
            self.write("server error")


class STATISTIC(tornado.web.RequestHandler):
    async def get(self):
        try:
            n = await self.settings["db"].storage.count_documents({})
            s = await self.settings["db"].storage.aggregate([{'$group': {'_id': None, 'sum':{'$sum':"$duplicates"}}}]).to_list(length=None)
            if len(s):
                s = s[0]['sum']
                res = {
                    "total_queries": s,
                    "unique_queries": n,
                    "percentage_of_duplicates": round((1- (n/s)) * 100, 2)
                }
            else:
                res = {
                    "total_queries": 0,
                    "unique_queries": 0,
                    "percentage_of_duplicates": 0
                }
            self.write(res)
        except:
            self.set_status(500)
            self.write("server error")
        

app = tornado.web.Application(
    [
        (r"/api/add", ADD),
        (r"/api/get", GET),
        (r"/api/update", PUT),
        (r"/api/remove", DELETE),
        (r"/api/statistic", STATISTIC)
    ],
    db=db,
)

if __name__ == "__main__":
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
