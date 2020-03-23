from app import db


class StockHolding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.String(20))
    stock_name = db.Column(db.String(50))
    stock_amount = db.Column(db.Numeric(20, 2))
    close_amount = db.Column(db.Numeric(20, 2))
    handling_fee = db.Column(db.Numeric(20, 2))
    money_spent = db.Column(db.Numeric(20, 2))
    buy_date = db.Column(db.String(20))

    def __repr__(self):
        return 'StockRecord {}, {}, {}, {}, {}, {}, {}, {}'.format(
            self.id, self.stock_id, self.stock_name,
            self.stock_amount, self.close_amount, self.handling_fee,
            self.money_spent, self.buy_date)
