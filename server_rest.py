import tornado.ioloop
import tornado.web
import random
import time

tokens = set()
last_token = 0

users = {}
last_user = 0

scooters = {}
last_scooter = 0

rental = {}
last_rental = 0

history_rental = {}
last_history_rental = 0

def generate_etag():
    return str(random.randint(0, 1000))

names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Isabella", "Jack"]
cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

for _ in range(30):
    last_user += 1
    last_scooter += 1
    users[str(last_user)] = {"uid": last_user, "name": random.choice(names), "city": random.choice(cities), "wallet": random.randint(100, 1000), "etag": generate_etag()}
    scooters[str(last_scooter)] = {"sid": last_scooter, "free": "1", "battery": random.randint(0, 100) , "longitude": random.randint(-180, 180) , "latitude": random.randint(-180, 180) , "price": random.randint(1, 5) ,"etag": generate_etag()}


class TokensHandler(tornado.web.RequestHandler):
    def get(self):
        global last_token 
        last_token += 1
        tokens.add(str(last_token))
        self.write(f"Token: {last_token}")


class RestHandler(tornado.web.RequestHandler):
    def _check_exist(self, objects, id):
        if id not in objects:
            self.set_status(404)
            self.write("Not found\n")
            return False
        return True
    
    def _check_ifmatch(self, if_match, etag):
        if not if_match:
            self.set_status(400)
            self.write("If-Match header is required for PUT requests\n")
            return False
        
        if if_match != etag:
            self.set_status(409)
            self.write("ETag mismatch: The resource has been modified since retrieved\n")
            return False
        return True
    
    def _check_is_all_args(self, list_args):
        for arg in list_args:
            if arg is None:
                self.set_status(400)
                self.write("Missing argument\n")
                return False
        return True
    
    def _change_val(self, object, vals):
        was_change = False
        for k, v in vals.items():
            if v and object[k] != v:
                object[k] = v
                was_change = True
        return was_change
    
    def _get_args(self, list_arg_name):
        args = {}
        for arg_name in list_arg_name:
            args[arg_name] = self.get_body_argument(arg_name, None)
        return args
    
    def _control_token(self, token, tokens):
        if not token or token not in tokens:
            self.set_status(400)
            self.write("Missing token\n" if not token else "Wrong token\n" )
            return False
        tokens.remove(token)
        return True


class UsersHandler(RestHandler):
    def get(self, uid=None):
        if uid:
            if self._check_exist(users, uid):
                self.write(users[uid])
        else:
            page = int(self.get_argument("page", default=1)) 
            per_page = int(self.get_argument("per_page", default=10))
            self.write({"users": list(users.values())[(page-1)*per_page: page*per_page]})

    def post(self, uid=None):
        if uid is not None:
            self.set_status(404)
            return        
        args = self._get_args(["name", "city", "wallet"])
        if not self._check_is_all_args(list(args.values())):
            return
        if not self._control_token(self.request.headers.get('X-Request-Token'), tokens):
            return
        global last_user
        last_user += 1
        args["uid"] = last_user
        args["etag"] = generate_etag()
        users[str(last_user)] = args
        self.write(args)

    def put(self, uid):
        if self._check_exist(users, uid) and self._check_ifmatch(self.request.headers.get('If-Match'), users[uid].get('etag')):         
            args = self._get_args(["name", "city", "wallet"])
            if not self._check_is_all_args(list(args.values())):
                return 
            if self._change_val(users[uid], args):
                users[uid]["etag"] = generate_etag()
            self.write(users[uid])

    def patch(self, uid):
        if self._check_exist(users, uid) and self._check_ifmatch(self.request.headers.get('If-Match'), users[uid].get('etag')):
            args = self._get_args(["name", "city", "wallet"])
            if self._change_val(users[uid], args):
                users[uid]["etag"] = generate_etag()
            self.write(users[uid])
    
    def delete(self, uid):
        if self._check_exist(users, uid):
            del users[uid]
            self.write(f"User deleted\n")


class ScootersHandler(RestHandler):
    def get(self, sid=None):
        if sid:
            if self._check_exist(scooters, sid):
                self.write(scooters[sid])
        else:
            page = int(self.get_argument("page", default=1)) 
            per_page = int(self.get_argument("per_page", default=10))
            self.write({"scooters": list(scooters.values())[(page-1)*per_page: page*per_page]})

    def post(self, sid=None):
        if sid is not None:
            self.set_status(404)
            return
        args = self._get_args(["battery", "longitude", "latitude", "price", "free"])
        if not self._check_is_all_args(list(args.values())):
            return
        if not self._control_token(self.request.headers.get('X-Request-Token'), tokens):
            return
        global last_scooter
        last_scooter += 1
        args["sid"] = last_scooter
        args["etag"] = generate_etag()
        scooters[str(last_scooter)] = args
        self.write(args)

    def put(self, sid):
        if self._check_exist(scooters, sid) and self._check_ifmatch(self.request.headers.get('If-Match'), scooters[sid].get('etag')):
            args = self._get_args(["battery", "longitude", "latitude", "price", "free"])
            if not self._check_is_all_args(list(args.values())):
                return
            if self._change_val(scooters[sid], args):
                scooters[sid]["etag"] = generate_etag()
            self.write(scooters[sid])

    def patch(self, sid):
        if self._check_exist(scooters, sid) and self._check_ifmatch(self.request.headers.get('If-Match'), scooters[sid].get('etag')):
            args = self._get_args(["battery", "longitude", "latitude", "price", "free"])
            if self._change_val(scooters[sid], args):
                scooters[sid]["etag"] = generate_etag()
            self.write(scooters[sid])
    
    def delete(self, sid):
        if self._check_exist(scooters, sid):
            del scooters[sid]
            self.write(f"Scooter deleted\n")


def rental_post_body(uid, sid):
    global last_rental
    last_rental += 1
    args = {"rid": last_rental, "uid": uid, "sid": sid, "start_time": round(time.time()), "end_time": -1, "price": 0, "etag": generate_etag()}
    rental[str(last_rental)] = args
    return args


def rental_delete_body(rid, check_exist):
    if check_exist(rental, rid):
        global last_history_rental
        last_history_rental += 1
        rental[rid]["hid"] = last_history_rental
        rental[rid]["end_time"] = round(time.time())
        if check_exist(users, rental[rid]["uid"]):
            users[rental[rid]["uid"]]["wallet"] -= int(rental[rid]["price"])
        history_rental[str(last_history_rental)] = rental[rid]
        deleted_rental = rental[rid]
        del rental[rid]
        return deleted_rental
    return False


class RentalHandler(RestHandler):
    def get(self, rid=None):
        if rid:
            if self._check_exist(rental, rid):
                self.write(rental[rid])
        else:
            page = int(self.get_argument("page", default=1)) 
            per_page = int(self.get_argument("per_page", default=10))
            self.write({"rental": list(rental.values())[(page-1)*per_page: page*per_page]})

    def post(self, rid=None):
        if rid is not None:
            self.set_status(404)
            return
        args = self._get_args(["uid", "sid"])
        if not self._check_is_all_args(list(args.values())) or not self._control_token(self.request.headers.get('X-Request-Token'), tokens):
            return
        if not self._check_exist(users, args["uid"]) or not self._check_exist(scooters, args["sid"]):
            return
        if scooters[args["sid"]]["free"] != "1":
            self.set_status(409)
            return
        scooters[args["sid"]]["free"] = "0"
        args = rental_post_body(args["uid"], args["sid"])  
        self.write(args)

    def put(self, rid):
        if self._check_exist(rental, rid) and self._check_ifmatch(self.request.headers.get('If-Match'), rental[rid].get('etag')):
            args = self._get_args(["uid", "sid", "start_time", "end_time", "price"])
            if not self._check_is_all_args(list(args.values())):
                return
            if self._change_val(rental[rid], args):
                rental[rid]["etag"] = generate_etag()
            self.write(rental[rid])

    def patch(self, rid):
        if self._check_exist(rental, rid) and self._check_ifmatch(self.request.headers.get('If-Match'), rental[rid].get('etag')):
            args = self._get_args(["uid", "sid", "start_time", "end_time", "price"])
            if self._change_val(rental[rid], args):
                rental[rid]["etag"] = generate_etag()
            self.write(rental[rid])
    
    def delete(self, rid):
        result = rental_delete_body(rid, self._check_exist)
        if result:
            scooters[result["sid"]]["free"] = "1"
            self.write(f"Rental deleted\n")


class HistoryRentalHandler(RestHandler):
    def get(self, hid=None):
        if hid:
            if self._check_exist(history_rental, hid):
                self.write(history_rental[hid])
        else:
            page = int(self.get_argument("page", default=1)) 
            per_page = int(self.get_argument("per_page", default=10))
            self.write({"history_rental": list(history_rental.values())[(page-1)*per_page: page*per_page]})


class RentalTransfersHandler(RestHandler):
    def post(self):
        args = self._get_args(["rid", "uid_new"])
        if not self._check_is_all_args(list(args.values())):
            return
        if not self._control_token(self.request.headers.get('X-Request-Token'), tokens):
            return
        if self._check_exist(rental, args["rid"]) and self._check_exist(users, args["uid_new"]):
            sid = rental[args["rid"]]["sid"]
            uid_new = args["uid_new"]
            rid = args["rid"]
            rental_delete_body(rid, self._check_exist)
            args = rental_post_body(uid_new, sid)
            self.write(args)
            return
        self.set_status(404)


if __name__ == "__main__":
    application = tornado.web.Application([
        ("/tokens", TokensHandler),
        ("/users(?:/([0-9]+))?", UsersHandler),
        ("/scooters(?:/([0-9]+))?", ScootersHandler),
        ("/rental(?:/([0-9]+))?", RentalHandler),
        ("/history-rental(?:/([0-9]+))?", HistoryRentalHandler),
        ("/rental-transfers", RentalTransfersHandler)
    ])
    application.listen(8000)
    tornado.ioloop.IOLoop.instance().start()