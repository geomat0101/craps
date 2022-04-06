#!/usr/bin/env python

import random


craps = [2,3,12]


class Win (Exception):
    pass


class Lose (Exception):
    pass


class Push (Exception):
    pass


class Bet (object):
    """
    Your run of the mill Don't Pass / Don't Come bet
    """

    point = None
    value = 0
    active = True


    def __init__ (self, value):
        """
        value is the amount bet on the line
        """
        self.value = value


    def applyRoll (self, total):
        """
        total is the sum of the dice
        """
        if not self.point:
            # come-out roll
            if total in craps:
                if total == 12:
                    # 12; don't pass pushes
                    print "bet pushes"
                    self.active = False
                    raise Push()
                else:
                    # 2,3; don't pass wins
                    self.win()
            elif total in [7, 11]:
                # 7,11; don't pass loses
                self.lose()
            else:
                # point is set
                self.point = total
                print "bet moves to the %d" % self.point
        else:
            # point already set
            if total == self.point:
                # point achieved; don't pass loses
                self.lose()
            elif total == 7:
                # 7; don't pass wins
                self.win()
            else:
                # nothing happens
                pass


    def win (self):
        print "bet (point=%s) wins" % self.point
        self.value *= 2
        self.active = False
        raise Win()


    def lose (self):
        print "bet (point=%s) loses" % self.point
        self.value = 0
        self.active = False
        raise Lose()


class BetSeries (object):
    """
    encapsulates a series of bets and rolls
    """

    bankroll = 0
    betUnit  = 0

    point = None

    dontpass = None
    dcBets = []


    def __init__ (self, bankroll, betUnit):
        """
        bankroll is the cash you bring to the table
        betUnit is the amount of each bet
        """
        self.bankroll = bankroll
        self.betUnit = betUnit
        print "bet Unit: $%8.2f" % betUnit
        print "bankroll: $%8.2f" % bankroll


    def roll (self):
        return(random.choice(range(1,7)), random.choice(range(1,7)))


    def comeout (self):
        print "come-out roll"
        print "bet on Don't Pass Line"
        self.dontpass = Bet(self.betUnit)
        self.bankroll -= self.betUnit
        print "bankroll: $%8.2f" % self.bankroll

        d1,d2 = self.roll()
        ttl = d1 + d2

        print "roll is: %2d" % ttl

        try:
            self.applyRoll(self.dontpass, ttl)
        except (Win, Lose, Push):
            return None

        return ttl


    def setFirstPoint (self):
        self.point = self.comeout()
        while not self.point:
            print "bankroll: $%8.2f" % self.bankroll
            self.point = self.comeout()

        print "point is: %d" % self.point


    def applyRoll (self, bet, total):
        """
        bet is a Bet() instance
        total is the dice roll total
        """
        try:
            bet.applyRoll(total)
        except (Win, Lose, Push):
            self.bankroll += bet.value
            raise

        return total


    def addDCBet (self):
        self.dcBets.append(Bet(self.betUnit))
        self.bankroll -= self.betUnit
        print "add a Don't Come bet"


    def run (self):
        self.setFirstPoint()
        needNewDontPass = False

        self.addDCBet()
        needNewDontCome = False

        shutItDown = False

        # first point and dc bet placed
        # now run the algo
        while True:
            d1,d2 = self.roll()
            ttl = d1+d2

            print "roll is: %2d" % ttl


            try:
                self.applyRoll(self.dontpass, ttl)
            except Win:
                if self.dontpass.point:
                    # 7: shutdown (everything wins or loses)
                    shutItDown = True
                else:
                    # 2,3 on come-out roll: replace don't pass
                    needNewDontPass = True
            except (Lose, Push):
                if ttl == 7:
                    # 7 shuts it down
                    shutItDown = True
                else:
                    # point; or 11,12 on come-out roll: replace dont pass bet immediately
                    needNewDontPass = True

            for bet in [ _ for _ in self.dcBets if _.active ]:
                try:
                    self.applyRoll(bet, ttl)
                except Win:
                    # 2,3: replace dont come bet immediately
                    needNewDontCome = True
                except Lose:
                    if not bet.point:
                        # 11: replace dont come bet immediately (7 causes series shutdown)
                        needNewDontCome = True
                except Push:
                    # 12: replace dont come bet immediately
                    needNewDontCome = True

            print "bankroll: $%8.2f" % self.bankroll

            # other: place new dont come bet every other roll
            if shutItDown:
                print "shutting down"
                return

            if needNewDontPass:
                needNewDontPass = False
                needNewDontCome = False
                print "add a new Don't Pass bet"
                self.dontpass = Bet(self.betUnit)
                self.bankroll -= self.betUnit
            else:
                if needNewDontCome:
                    self.addDCBet()
                    needNewDontCome = False
                else:
                    print "skipping DC Bet"
                    needNewDontCome = True

            print "bankroll: $%8.2f" % self.bankroll


if __name__ == '__main__':
    series = BetSeries(0, 25)
    series.run()
    print "final bankroll: $%8.2f" % series.bankroll

