import json


class EtsyOAuthScope:
    def __init__(self, from_json_str=None):
        if from_json_str is not None:
            decode = json.loads(from_json_str)
            self.options = decode.get('options', None)
        else:
            self.options = dict({
                'address_r': False,
                'address_w': False,
                'billing_r': False,
                'cart_r': False,
                'cart_w': False,
                'email_r': False,
                'favorites_r': False,
                'favorites_w': False,
                'feedback_r': False,
                'listings_d': False,
                'listings_r': False,
                'listings_w': False,
                'profile_r': True, # Default
                'profile_w': False,
                'recommend_r': False,
                'recommend_w': False,
                'shops_r': False,
                'shops_w': False,
                'transactions_r': False,
                'transactions_w': False,
            })

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def __repr__(self):
        return self.toJSON()
    def __getitem__(self, item):
        return self.options[item]

    def __setitem__(self, key, value):
        self.options[key] = value

    def __str__(self):
        return ' '.join([key for key, value in self.options.items() if value])
