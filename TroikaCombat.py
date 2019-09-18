# This is a tool for tracking combat initiative for the the RPG system "Troika!"

# A description of what operation looks like and what the program is internally doing.
# User (the GM) starts the program by dragging the PC list onto it.
#   That's just a list of names and initiative counts each - usually 2.
# Creates the TABLE. It's a list of everything pulled out of the bag, in order.
# "Main" loop begins.
# Check for bags: No bags: create new bag: preload with contents of PC list file and an end-of-round-token.
#   If no file was given, the bag will have just an end-of-round token.
# It declares what was done.
# Ends loop by declaring what's in the current active bag and prompts the user for input.
# 1x loop: User populates the bag with enemies. E.g. add 20 Goblin
# 1x loop each: User pulls tokens from the bag one at a time.
# 1x loop each: User kills dead actors. These tokens are removed when the next round would begin.
# The end of round token is pulled just like any other.
# Eventually, user says "next", the bag is refilled, minus tokens from killed creatures.

# Bits of flair: It prints in colour. It assigns an essentially-random but deterministic colour to each token by name.
# The PC list file is formatted as follows:
# 2 Curly
# 2 Larry
# 2 Moe
# 3 Alacritous Steve
# 1 Boblin the Goblin
# 8 The Invisible Dragon That The Party Doesn't Know Is Following Them
# You CAN modify this file without restarting the program and it WILL take changes into account for the next bag.

# Valid inputs!
# help: display all valid commands and the syntax for each. It just displays everything, no specificity.
# add [number] [name]: adds X tokens to the bag, under the given name e.g. "Goblin", "Flood".
# a: shorthand for add
# remove [number] [name]: removes X of the specified token from the BAG first, then the table: for fixing errors!
# kill [number] [name]: makes a note to remove that many tokens AFTER repopulating
# k: shorthand for kill
# pull: remove a random token from the bag, state it clearly, and put it on the table.
# '': shorthand for pull
# next: next round. Puts all tabled tokens back in the bag, minus killed ones.
# quit: quits the program. Asks for confirmation.

# Path should be:
# C:\Users\jonmw\PycharmProjects\troika-tracker\TroikaTest.txt

from collections import Counter
import random
import sys
from sty import fg, bg, ef, rs

class Bag:
    def __init__(self):
        # Todo: find a way to add tokens to the bag, from a premade file, AFTER you start.
        # Todo: the kill method. You bank removals for later. Any ideas for ease for tokens/enemy?
        # Todo: GUI this shit up. That's gotta be nicer to use.
        self.contents = Counter()  # It counts things. It's a counter.
        print("Creating a new bag...")
        self.table = Counter()  # See above
        self.colour_lookup = {}
        self.turnOrder = []
        self.add(['add', 'End of Round', '1'])
        try:
            preload_path = sys.argv[1]
            with open(preload_path) as f:
                raw_preload = f.read(512)
            trimmed_instructions = [line.strip() for line in raw_preload.splitlines() if (len(line.strip()) > 0)]
            for line in trimmed_instructions:
                instruction = ['add'] + line.split(' ')
                self.add(instruction)
        except Exception as e:
            print("No usable preload file found:" + str(e))

    def report(self):
        print("\nBag contains:")
        if len(self.contents) == 0:
            print("Absolutely nothing!")
        else:
            for k, v in self.contents.items():
                print(fg(*self.colour_lookup[k]) + "{}x {}".format(v, k) + fg.rs)
        print("\nOn the table:")
        if len(self.table) == 0:
            print("Absolutely nothing!")
        else:
            for k, v in self.table.items():
                print("{}: {}".format(k, v))

    def add(self, c_split):
        order = self.extract_counter(c_split)
        try:
            for k, v in order.items():
                # This might be a new token: check if it's got an associated colour.
                if k not in self.colour_lookup.keys():
                    self.colour_lookup[k] = self.colourise(k)
                else:
                    pass

                # At the moment each order can only give one key-value pair.
                # Seems weird to do this in a for loop but I don't know how to do it otherwise.
                print(fg(*self.colour_lookup[k]) + "Tokens going into the bag: {}x {}".format(v, k) + fg.rs)

            self.contents += order
        except Exception as e:
            print("Adding token failed!" + str(e))
            print("Required format: add [token name] [amount to add, default 1]")
        self.report()

    def remove(self, c_split):
        order = self.extract_counter(c_split)
        try:
            possible_removals = self.contents & order
            for k, v in possible_removals.items():
                # At the moment each order can only give one key-value pair.
                # Seems weird to do this in a for loop but I don't know how to do it otherwise.
                print(fg(*self.colour_lookup[k]) + "Removing tokens from the bag: {}x {}".format(v, k) + fg.rs)
            self.contents -= possible_removals
        except Exception as e:
            print("Removing token failed!" + str(e))
            print("Required format: add [token name] [amount to take, default 1000]")
        self.report()

    def pull(self):
        # Select a random key in self.contents, by weight according to value
        if len(self.contents) > 0:
            # This line is hella elegant and took some study to understand it.
            type_grabbed = random.choices(*zip(*self.contents.items()))[0]
            # I could reuse the "remove" function and write a new function for adding a token to the table...
            # But I think writing 3 lines here should be fine.
            cnt = Counter({type_grabbed: 1})
            self.turnOrder.append(type_grabbed)
            self.contents -= cnt
            self.table += cnt
            print(fg(*self.colour_lookup[type_grabbed]) + "{} holds the initiative!".format(type_grabbed.upper()) + fg.rs)
        else:
            print("Can't pull anything; the bag is empty!")
        pass

    def next(self):
        self.contents += self.table
        self.table.clear()
        print("Starting a new round!")
        self.report()
        self.turnOrder.append("NEW ROUND BEGINS")
        pass

    def turns(self):
        for i, v in enumerate(self.turnOrder):
            print("{}: {}".format(i, v))

    def extract_counter(self, command):
        try:
            if command[-1].isdigit():
                num_tokens = int(command.pop())  # valid command received
            elif command[0] == "add":
                # the default amount for add is 1
                num_tokens = 1
            elif command[0] == "remove":
                num_tokens = 1000
            else:
                num_tokens = 1  # Setting a default here for every other case
                # Because I don't HAVE any other instructions that should need this yet.
            name_token = " ".join([word.capitalize() for word in command[1:]])
            return Counter({name_token: num_tokens})
        except Exception as e:
            print("Malformed command!" + str(e))
            print("That command needs [instruction] [token name (spaces OK)] [optional: number of tokens]")
            return 0

    def colourise(self, token_name):
        randstate = random.getstate()
        random.seed(a=token_name)
        while True:
            clr = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
            if (clr[0] * 3 // 4 + clr[1] + clr[2] // 2) > 230:
                break
            else:
                pass
        random.setstate(randstate)
        return clr


# PROGRAM START
print("\nThis is an initiative-managing program for Troika!")
print("Troika!'s initiaive system involves having a lot of tokens in a bag and drawing them out one at a time.")
print("Whoever's token gets pulled out gets to take a turn. If the End of Round token is pulled, refill the bag.")
print("Heroes get 2 tokens each. Hirelings get 1 each. Monsters range from 1 to 8.")
random.seed(a=123)
baglist = []
valid_commands = ['help', 'quit', 'add', 'remove', 'pull', 'check', 'next', 'turns', '']
# see if we got initialised with a data file

while True:
    if len(baglist) == 0:
        print("No bags found. Rectifying that.")
        baglist.append(Bag())
        b = baglist[0]

    try:
        instruction = input("[Do what?]> ")
        c_split = instruction.split(' ')
        c_split[0] = c_split[0].lower()
        action = c_split[0]
        assert action in valid_commands
        # In the most general terms, the input looks usable
        if action == 'help':
            print("Commands: help, quit, add [token, number=1], remove [token, number=1], pull, check, next, turns")
            print("Giving an empty string (just hitting Enter) will also pull a token.")
        if action == 'quit':
            print("Quitting... ")
            break
        if action == 'add':
            b.add(c_split)
        if action == 'remove':
            b.remove(c_split)
        if (action == 'pull') or (action == ''):
            b.pull()
        if action == 'check':
            b.report()
        if action == 'next':
            b.next()
        if action == 'turns':
            b.turns()
    except Exception as e:
        print("Invalid input!" + str(e))
        print("Valid commands:", ', '.join(valid_commands))

print("Program over.")
