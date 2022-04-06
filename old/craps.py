#!/usr/bin/env python

import random, time

debug = False

simulation_max = 10000	# max iterations, 0 = forever

use_place_bets = False
keep_place_bets_working = True

numbers = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]

# what does buying odds cost for a particular number (passline / come cost not incl)?

# no odds
#odds_cost = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# using 3x for 4,10;  4x for 5,9;  5x for 6,8 5 minimum
#odds_cost = [0, 0, 0, 0, 15, 20, 25, 0, 25, 20, 15, 0, 0]
# 3x4x5x 10 minimum
odds_cost = [0, 0, 0, 0, 30, 40, 50, 0, 50, 40, 30, 0, 0]
# 5x 10 min
#odds_cost = [0, 0, 0, 0, 50, 50, 50, 0, 50, 50, 50, 0, 0]

# buy odds on numbers in this priority order
# fixme: unimplemented
odds_priority = [4,10,5,9,6,8]


# how much do you win for winning a point (or come) for a particular number (odds winnings incl)

# no odds, 10 min
#winnings = [0, 0, 0, 0, 20, 20, 20, 0, 20, 20, 20, 0, 0]
# 3x4x5x 5 minimum
#winnings = [0, 0, 0, 0, 55, 60, 65, 0, 65, 60, 55, 0, 0]
# 3x4x5x 10 minimum
winnings = [0, 0, 0, 0, 110, 120, 130, 0, 130, 120, 110, 0, 0]
# 5x 10 min
#winnings = [0, 0, 0, 0, 170, 145, 130, 0, 130, 145, 170, 0, 0]

# 5 min
#passline_cost = come_cost = field_cost = 5
# 10 min
passline_cost = come_cost = field_cost = 10

craps = [2, 3, 12]

bets = {}
come = False

working_numbers = [4,5,6,8,9,10]
#working_numbers = [4,5,9,10]
working_counter = 0	# refcount for come bets on working_numbers.  Only want 3 of those working at a time.
working_limit = 3		# no more than this many working at once

use_field_bets = False
field_numbers = [2,3,4,9,10,11,12]
field = False

def clear_bets():
	global bets
	bets = {
		'come': {
				'four': False,
				'five': False,
				'six': False,
				'eight': False,
				'nine': False,
				'ten': False
			},
		'place': {
				'four': 0,
				'five': 0,
				'six': 0,
				'eight': 0,
				'nine': 0,
				'ten': 0
			}
		}

clear_bets()

def roll ():
	return(random.choice(range(1,7)), random.choice(range(1,7)))

def debug_print (msg):
	global debug
	if debug:
		print(msg)


point = None
low_balance = high_balance = balance = 1000
bust_count = 0
boom_count = 0
roll_count = 0
simulation_count = 0

while True:
	
	if balance < low_balance:
		low_balance = balance
	if balance > high_balance:
		high_balance = balance

	if balance < 100 or balance > 1500:
		# record results and restart
		if balance < 100:
			res = 'bust'
			bust_count += 1
		else:
			res = 'boom'
			boom_count += 1
		clear_bets()
		working_counter = 0
		point = None
		print("rolls: %5d, result: %s, lowbal: %7.2f, highbal: %7.2f, total busts: %5d, total booms: %5d, success rate: %0.2f %%" % (roll_count, res, low_balance, high_balance, bust_count, boom_count, (100 * float(boom_count) / (boom_count + bust_count))))
		low_balance = high_balance = balance = 1000
		roll_count = 0
		simulation_count += 1
		if simulation_max and simulation_count >= simulation_max:
			break
#		time.sleep(0.1)

	# roll
	roll_count += 1
	d1,d2 = roll()
	ttl = d1+d2

	if debug:
		debug_print("? ")
		ttl = int(raw_input())

	if not point:
		# coming out

		# pass line bet
		debug_print("pass line bought")
		balance -= passline_cost

		if ttl in craps:
			# lose, reset
			debug_print("craps %d" % ttl)
			continue

		if ttl in [7,11]:
			# win 5 on passline, reset
			debug_print("pass line wins (%d)" % ttl)
			balance += (passline_cost * 2)

			if ttl == 7:
				# come, place bets seven out
				debug_print("come, place bets seven out; bets cleared")
				clear_bets()
				working_counter = 0

			continue

		# point has been set
		point = ttl
		debug_print("point set to %d; odds bought (%d)" % (point, odds_cost[ttl]))

		if point in working_numbers:
			working_counter += 1

		# place bet up?
		if bets['place'][numbers[point]]:
			debug_print("existing place bet comes down (working = %s)" % keep_place_bets_working)
			if keep_place_bets_working:
				# it won too
				balance += 7 * bets['place'][numbers[point]]

			if point in [6,8]:
				balance += 6 * bets['place'][numbers[point]]
			elif point in [5,9]:
				balance += 5 * bets['place'][numbers[point]]
			bets['place'][numbers[point]] = 0
		
		# check winnings on any active come bets and buy odds behind the line
		balance -= odds_cost[ttl]
		if bets['come'][numbers[ttl]]:
			debug_print("come bet wins")
			balance += winnings[ttl]
			bets['come'][numbers[ttl]] = False
			if ttl in working_numbers:
				working_counter -= 1

		# buy come bet?
		if working_counter < working_limit:
			debug_print("new come bet bought")
			come = True
			balance -= come_cost
		else:
			if use_field_bets and not field:
				# place a field bet if we have 3/3 of [5,6,8]
				midcount = 0
				if bets['come']['five']:
					midcount += 1
				if bets['come']['six']:
					midcount += 1
				if bets['come']['eight']:
					midcount += 1
				if point in [5,6,8]:
					midcount += 1
				if midcount > 2:
					debug_print("field bet bought")
					balance -= field_cost
					field = True

		# place bets
		if point != 6 and not bets['place']['six'] and not bets['come']['six'] and use_place_bets:
			debug_print("6 placed on 6")
			balance -= 6
			bets['place']['six'] = 1

		if point != 8 and not bets['place']['eight'] and not bets['come']['eight'] and use_place_bets:
			debug_print("6 placed on 8")
			balance -= 6
			bets['place']['eight'] = 1
	
	else:
		# point has been set previously

		if use_field_bets and field:
			if ttl in field_numbers:
				debug_print("field bet wins")
				if ttl in [2,12]:
					balance += (field_cost * 3)
				else:
					balance += (field_cost * 2)
			# field always comes down
			field = False

		if ttl == 7:
			# seven out, come gets paid
			debug_print("seven out; bets cleared")
			point = None
			clear_bets()
			working_counter = 0
			if come:
				debug_print("come gets some")
				balance += (come_cost * 2)
				come = False
		elif ttl == 11:
			# come gets paid
			if come:
				debug_print("eleven: come gets paid; re-bought")
				balance += come_cost
		elif ttl in craps:
			# come craps out
			if come:
				debug_print("come craps out (%d); re-bought" % ttl)
				balance -= come_cost
		elif ttl == point:
			# point has been achieved
			debug_print("point has been achieved")
			point = None
			balance += winnings[ttl]

			if ttl in working_numbers:
				working_counter -= 1

			# move come to the number, buy the odds on it
			if come:
				debug_print("come bet moved to %d; odds bought (%d)" % (ttl, odds_cost[ttl]))
				balance -= odds_cost[ttl]
				bets['come'][numbers[ttl]] = True
				come = False
				if ttl in working_numbers:
					working_counter += 1
		else:
			# is there a bet on it already?
			if bets['come'][numbers[ttl]]:
				debug_print("come bet wins on %d" % ttl)
				balance += winnings[ttl]
				bets['come'][numbers[ttl]] = False
				if ttl in working_numbers:
					working_counter -= 1

			if bets['place'][numbers[ttl]]:
				# no place bets made on 4,10 so payouts will be 7 * units
				debug_print("place bet wins on %d" % ttl)
				balance += 7 * bets['place'][numbers[ttl]]
				if not come:
					# up one unit
					debug_print("up one unit")
					bets['place'][numbers[ttl]] += 1
					balance -= 5
					if ttl in [6,8]:
						# 6,8 costs 6
						balance -= 1
				else:
					# take it down
					debug_print("come bet incoming, taking down the place bet")
					if ttl in [6,8]:
						balance += 6 * bets['place'][numbers[ttl]]
					else:
						# 5,9
						balance += 5 * bets['place'][numbers[ttl]]
					bets['place'][numbers[ttl]] = 0

			if come:
				debug_print("come bet moves to %d; odds bought (%d)" % (ttl, odds_cost[ttl]))
				come = False
				bets['come'][numbers[ttl]] = True
				balance -= odds_cost[ttl]
				if ttl in working_numbers:
					working_counter += 1

			if working_counter < working_limit:
				# buy a new come
				debug_print("new come bet bought")
				balance -= come_cost
				come = True
			else:
				if use_place_bets:
					# extra place bet spot open on the 5,9?
					for n in [5,9]:
						if not bets['come'][numbers[n]] and not bets['place'][numbers[n]]:
							debug_print("adding a place bet on %d" % n)
							balance -= 5
							bets['place'][numbers[ttl]] = 1
				if use_field_bets and not field:
					# place a field bet if we have 3/3 of [5,6,8]
					midcount = 0
					if bets['come']['five']:
						midcount += 1
					if bets['come']['six']:
						midcount += 1
					if bets['come']['eight']:
						midcount += 1
					if point in [5,6,8]:
						midcount += 1
					if midcount > 2:
						debug_print("field bet bought")
						balance -= field_cost
						field = True


	debug_print("roll: %d, point: %s, balance: %0.2f, outside_nums: %d" % (ttl, point, balance, working_counter))







