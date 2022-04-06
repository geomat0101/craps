#!/usr/bin/env python

from pprint import pformat as pf, pprint as pp
import random

class Roll (object):
    """ one roll of two dice """

    def __init__ (self):
        self.dieOne = random.choice(range(1,7))
        self.dieTwo = random.choice(range(1,7))

    @property
    def roll (self):
        return self.dieOne + self.dieTwo

    @property
    def hard (self):
        return (self.dieOne == self.dieTwo)

    def __repr__ (self):
        return "Roll: %d (%d, %d)" % (self.roll, self.dieOne, self.dieTwo)




class BankRoll (object):
    """ cash accounting and active bet manager """

    numWords = "zero one two three four five six seven eight nine ten eleven twelve".split()

    def __init__ (self, startAmount=500):
        self.total = float(startAmount)
        self.bets = set()
        self.fieldBet = None
        self.placeBets = {
                "four": None,
                "five": None,
                "six": None,
                "eight": None,
                "nine": None,
                "ten": None
                }
        print self

    def __repr__ (self):
        return "BankRoll: $%5.2f" % self.total

    def makeBet (self, bet):
        self.total -= bet.amount
        bet.active = True
        self.bets.add(bet)
        if isinstance(bet, BetField):
            self.fieldBet = bet
        print "BET: %s" % bet
        print self

    def takedownBet (self, bet):
        self.total += bet.amount
        bet.active = False
        if bet in self.bets:
            self.bets.remove(bet)
        if isinstance(bet, BetField):
            self.fieldBet = None
        print "BankRoll - Bet Taken Down: %s" % bet
        print self

    def betWon (self, bet):
        # assume everything comes down every time for now
        if not bet.active:
            raise BetInactive

        self.total += bet.payout()
        self.total += bet.amount
        self.bets.remove(bet)
        print self

        if isinstance(bet, BetPlace):
            self.placeBets[self.numWords[bet.point]] = None
        bet.active = False

        if isinstance(bet, (BetPassline, BetOdds)):
            # point is off
            BetPlace.working = False

        if isinstance(bet, BetPlace):
            if bet.amount < 13:
                # full press
                newbet = BetPlace(bet.amount * 2, bet.point)
                self.makeBet(newbet)
                self.placeBets[self.numWords[bet.point]] = newbet
            else:
                # up one unit and maybe field
                if bet.point == 5:
                    newbet = BetPlace(bet.amount + 5, bet.point)
                    self.makeBet(newbet)
                    self.placeBets[self.numWords[bet.point]] = newbet
                elif bet.point in [6,8]:
                    newbet = BetPlace(bet.amount + 6, bet.point)
                    self.makeBet(newbet)
                    self.placeBets[self.numWords[bet.point]] = newbet
                else:
                    raise "Unimplemented"

        elif isinstance(bet, BetField):
            if BetPlace.working:
                if bet.inTheMoney:
                    newbet = BetField(bet.amount + 5)
                else:
                    newbet = BetField(5)
                newbet.inTheMoney = True
                self.makeBet(newbet)
            else:
                self.fieldBet = None


    def betLost (self, bet):
        if not bet.active:
            raise BetInactive

        self.bets.remove(bet)
        bet.active = False
        if isinstance(bet, BetField):
            self.fieldBet = None

    def resolveRoll (self, roll):
        print "ROLL: %s" % roll
        winnings = 0.0
        for bet in list(self.bets):
            if not bet.working:
                continue

            try:
                bet.resolve(roll.roll)
            except BetWon:
                payout = bet.payout()
                print "WINNER: +%5.2f %s" % (payout, bet)
                self.betWon(bet)
                winnings += payout
            except BetLost:
                print "LOSER: %s" % bet
                self.betLost(bet)

        # make sure field is up unless we just wiped or point is off
        if self.bets and not self.fieldBet and BetPlace.working:
            if winnings > 15 or winnings == 0.0:
                # allow full press on place bet instead of field, or buy back into the field when idle
                self.makeBet(BetField(5))
            else:
                print "NO FIELD: winnings were only %5.2f" % winnings



class BetUnresolved (Exception):

    def __init__ (self):
        return



class BetWon (Exception):

    def __init__ (self):
        return



class BetLost (Exception):

    def __init__ (self):
        return



class BetInactive (Exception):

    def __init__ (self):
        return



class Bet (object):
    """ base encapsulation of a single bet """

    working = True  # class level attribute which flips on and off with the point
                    # bets are not resolved when not working

    def __init__ (self, amount):
        self.amount = float(amount)
        self.active = False
    
    def payout (self):
        """ must be defined by subclasses, returns payout w/o initial cash at risk """
        return 0.0

    def resolve (self, point):
        """ may be defined by subclasses, raises win/lose exceptions """
        if not self.active:
            raise BetInactive

        if point == 7:
            self.point = 13 # seven-out
            raise BetLost

        if point == self.point:
            raise BetWon



class BetPassline (Bet):

    def __init__ (self, amount):
        Bet.__init__(self, amount)
        self.point = None

    def payout (self):
        if not self.point:
            raise BetUnresolved

        if self.point in [2,3,12,13]:
            # 13 is a magic token for "seven-out"
            # 7 means we won an initial passline roll
            return 0.0

        return self.amount


    def resolve (self, point):
        if not self.active:
            raise BetInactive

        if not self.point:
            # initial passline roll
            self.point = point
            if point in [7,11]:
                raise BetWon
            if point in [2,3,12]:
                raise BetLost
            return

        if point == 7:
            self.point = 13
            raise BetLost

        if point == self.point:
            raise BetWon


    def __repr__ (self):
        return "Bet - Passline: $%5.2f; point: %s" % (self.amount, self.point)



class BetOdds (Bet):

    def __init__ (self, amount, point):
        assert point in [4,5,6,8,9,10]
        Bet.__init__(self, amount)
        self.point = point

    def payout (self):
        if self.point in [4,10]:
            # 2:1
            return self.amount * 2

        if self.point in [5,9]:
            # 3:2
            return self.amount * 3 / 2

        if self.point in [6,8]:
            # 6:5
            return self.amount * 6 / 5

        if self.point == 13:
            # seven-out
            return 0.0

    def __repr__ (self):
        return "Bet - Odds: $%5.2f; point: %s" % (self.amount, self.point)



class BetPlace (Bet):

    def __init__ (self, amount, point):
        assert point in [4,5,6,8,9,10]
        Bet.__init__(self, amount)
        self.point = point

    def payout (self):
        if self.point == 13:
            return 0.0

        if self.point in [4,10]:
            # 9:5
            return self.amount * 9 / 5

        if self.point in [5,9]:
            # 7:5
            return self.amount * 7 / 5

        if self.point in [6,8]:
            # 7:6
            return self.amount * 7 / 6

    def __repr__ (self):
        return "Bet - Place: $%5.2f; point: %s" % (self.amount, self.point)



class BetField (Bet):

    def __init__ (self, amount, tripleOnTwelve=True):
        Bet.__init__(self, amount)
        self.tripleOnTwelve = tripleOnTwelve
        self.point = None
        self.inTheMoney = False # this is so we can place same bet first time around before pressing


    def payout (self):
        # 2x on 2, 2x or 3x on 12, 1x on rest
        if not self.point:
            raise BetUnresolved

        if self.point == 13:
            return 0.0

        if self.point == 12:
            if self.tripleOnTwelve:
                return self.amount * 3
            else:
                return self.amount * 2

        if self.point == 2:
            return self.amount * 2

        return self.amount


    def resolve (self, point):
        if not self.active:
            raise BetInactive

        if point in [2,3,4,9,10,11,12]:
            self.point = point
            raise BetWon

        if point in [5,6,7,8]:
            self.point = 13
            raise BetLost

    def __repr__ (self):
        return "Bet - Field: $%5.2f; point: %s" % (self.amount, self.point)





if __name__ == "__main__":
    point = None
    placeBets = {
            "four": None,
            "five": None,
            "six": None,
            "eight": None,
            "nine": None,
            "ten": None
            }

    br = BankRoll()
    BetPlace.working = False

    def oneSeries ():
        global point
        # come out roll
        # place passline bets until a point is set
        while True:
            if not point:
                br.makeBet(BetPassline(10))
            r = Roll()
            br.resolveRoll(r)
            if r.roll not in [2,3,7,11,12]:
                point = r.roll
                print "POINT IS %d" % r.roll
                break

        # point is set, now make odds and check field / place bets
        # odds
        BetPlace.working = True

        if point in [4,6,8,10]:
            br.makeBet(BetOdds(25, point))
        elif point in [5,9]:
            br.makeBet(BetOdds(26, point))

        # place bets
        # check for winners/losers and clear up placeBets dict
        for k,v in br.placeBets.iteritems():
            if v not in br.bets:
                br.placeBets[k] = None

        # initial field
        if not br.fieldBet:
            br.makeBet(BetField(5))

        # if 5,6,8 are up; let them ride unless that's the point; else down
        if point == 5:
            if br.placeBets["five"]:
                br.takedownBet(br.placeBets["five"])
                br.placeBets["five"] = None
            if not br.placeBets["six"]:
                br.placeBets["six"] = BetPlace(12, 6)
                br.makeBet(br.placeBets["six"])
            if not br.placeBets["eight"]:
                br.placeBets["eight"] = BetPlace(12, 8)
                br.makeBet(br.placeBets["eight"])
        elif point == 6:
            if not br.placeBets["five"]:
                br.placeBets["five"] = BetPlace(10, 5)
                br.makeBet(br.placeBets["five"])
            if br.placeBets["six"]:
                br.takedownBet(br.placeBets["six"])
                br.placeBets["six"] = None
            if not br.placeBets["eight"]:
                br.placeBets["eight"] = BetPlace(12, 8)
                br.makeBet(br.placeBets["eight"])
        elif point == 8:
            if not br.placeBets["five"]:
                br.placeBets["five"] = BetPlace(10, 5)
                br.makeBet(br.placeBets["five"])
            if not br.placeBets["six"]:
                br.placeBets["six"] = BetPlace(12, 6)
                br.makeBet(br.placeBets["six"])
            if br.placeBets["eight"]:
                br.takedownBet(br.placeBets["eight"])
                br.placeBets["eight"] = None
        else:
            if not br.placeBets["five"]:
                br.placeBets["five"] = BetPlace(10, 5)
                br.makeBet(br.placeBets["five"])
            if not br.placeBets["six"]:
                br.placeBets["six"] = BetPlace(12, 6)
                br.makeBet(br.placeBets["six"])
            if not br.placeBets["eight"]:
                br.placeBets["eight"] = BetPlace(12, 8)
                br.makeBet(br.placeBets["eight"])

        print "\nAll bets:\n%s\n" % pf(br.bets)
                
        while point:
            r = Roll()
            br.resolveRoll(r)
            if r.roll in [7, point]:
                point = None
                print "POINT IS OFF"
                BetPlace.working = False
                if br.fieldBet:
                    br.takedownBet(br.fieldBet)
                for bet in list(br.bets):
                    if bet.amount > 25.00:
                        br.takedownBet(bet)
                print "\nRemaining bets:\n%s\n" % pf(br.bets)
                print br

            
    boom = bust = 0
    for i in range(1000):
        br = BankRoll()
        BetPlace.working = False
        highbal = lowbal = br.total
        while 250.0 < br.total < 750.0:
            oneSeries()
            if br.total > highbal:
                highbal = br.total
            if br.total < lowbal:
                lowbal = br.total

        print (lowbal, highbal)

        if br.total <= 250.:
            bust += 1
        else:
            boom += 1

        print (boom, bust)




