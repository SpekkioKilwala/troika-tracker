# This is a tool for tracking combat initiative for the the RPG system "Troika!"

# A description of what example operation looks like and what the program is internally doing.
# User (the GM) can start the script by dragging a text file onto it (FEATURE DEPRECATED; STILL WORKS BUT NOT STANDARD)
#   That's just a list of names and initiative counts each (often 2), no commas, in a .txt.
#   The new recommended method is to follow a YAML structure and the "save" and "load" commands.
# "Main" loop begins.
# Check for bags: No bags: create new bag: preload with contents of PC list file and an end-of-round-token.
#   If no file was given, the bag will have just an end-of-round token.
# It declares what was done and displays the state of the bag.
# Ends loop by declaring what's in the current active bag and prompts the user for input.
# 1x loop: User populates the bag with enemies. E.g. add 20 Goblin
# 1x loop each: User pulls tokens from the bag one at a time.
# 1x loop each: User kills dead actors. These tokens are removed when the next round would begin. NOT YET IMPLEMENTED!
# The end of round token is pulled just like any other.
# Eventually, user says "next", the bag is refilled, minus tokens from killed creatures.

# Bits of flair: It prints in colour. It assigns an essentially-random but deterministic colour to each token by name.
# A sample preload YAML file is given as follows.
# Curly: 2
# Larry: 2
# Moe: 2
# Alacritous Steve: 3
# Boblin the Goblin: 1
# The Invisible Dragon That The Party Doesn't Know Is Following Them: 8

# Valid inputs!
# help: display all valid commands and the syntax for each. It just displays everything, no specificity.
# add [name] [number (optional)]: adds X tokens to the bag, under the given name e.g. "Goblin", "Flood".
# remove [number] [name]: removes X of the specified token from the BAG only.
# pull: remove a random token from the bag, state it clearly, and put it on the table.
# '': shorthand for pull
# next: next round. Puts all tabled tokens back in the bag, minus killed ones.
# quit: quits the program. Asks for confirmation.
# load: load a yaml file
# save: save to a yaml file
# check: reports on bag contents

# Features coming!
# Rerolling a token's colour, and preserving those changes. Complexifies token data.
# Kill function. E.g. "kill dragon" will remove exactly 8 tokens from a 24-token 3-dragon fight for NEXT round.
# That obviously also will complexify the token data.

# Todo: Make it so that the load() function doesn't replicate code from other functions e.g. colouring and report.
# Todo: Clean up warts: PEP8 or at least a consistent style; rename junk variables appropriately e.g. use _.

from collections import Counter
import random
import sys, os
from sty import fg, bg, ef, rs
import yaml

class Bag:
    def __init__(self):
        self.contents = Counter()  # It counts things. It's a counter.
        print("Creating a new bag...")
        self.table = Counter()  # See above
        self.nextRoundRemovals = Counter()  # It gets reported on so it needs to be declared very early
        self.colour_lookup = {}
        self.turnOrder = []
        # First problem: the script working directory shouldn't really be bag-specific.
        # Second problem: the YAML code doesn't necessarily save to the location of the script in any case!
        self.workingDir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.add(['End of Round', '1'])
        # Should I remove this? It's not breaking anything.
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
                print(fg(*self.colour_lookup[k]) + "{}x {}".format(v, k) + fg.rs)
        print("\nNext round will be cleared out:")
        if len(self.nextRoundRemovals) == 0:
            print("Absolutely nothing!")
        else:
            for k, v in self.nextRoundRemovals.items():
                print(fg(*self.colour_lookup[k]) + "{}x {}".format(v, k) + fg.rs)

    def add(self, c_split):
        try:
            if c_split[-1].isnumeric():  # Remember the last element is taken as a QUANTITY if it is numeric
                assert len(c_split) > 1  # Ensure we'll still have something usable as a name after removing that
            else:
                assert len(c_split) > 0  # We must have a nonzero amount of instruction to act on
            order = self.extract_counter(c_split, default=2)
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
        # This is set to prioritise removing things from the BAG FIRST.
        # It is for changing the initiative OUTSIDE combat or for correcting errors, not during combat!
        try:
            if c_split[-1].isnumeric():  # Remember the last element is taken as a QUANTITY if it is numeric
                assert len(c_split) > 1  # Ensure we'll still have something usable as a name after removing that
            else:
                assert len(c_split) > 0  # We must have a nonzero amount of instruction to act on
            order = self.extract_counter(c_split, default=1000)
            possible_removals = self.contents & order
            possible_table_removals = (order - possible_removals) & self.table
            for k, v in possible_removals.items():
                # At the moment each order can only give one key-value pair.
                # Seems weird to do this in a for loop but I don't know how to do it otherwise.
                print(fg(*self.colour_lookup[k]) + "Removing tokens from the bag: {}x {}".format(v, k) + fg.rs)
            self.contents -= possible_removals
            for k, v in possible_table_removals.items():
                # Second verse, same as the first
                print(fg(*self.colour_lookup[k]) + "Removing tokens from the table: {}x {}".format(v, k) + fg.rs)
            self.table -= possible_table_removals
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

    def kill(self, c_split):
        try:
            if c_split[-1].isnumeric():  # Remember the last element is taken as a QUANTITY if it is numeric
                assert len(c_split) > 1  # Ensure we'll still have something usable as a name after removing that
            else:
                assert len(c_split) > 0  # We must have a nonzero amount of instruction to act on
            order = self.extract_counter(c_split, default=1000)
            self.nextRoundRemovals += order
        except Exception as e:
            print("That cannot be killed." + str(e))

    def next(self):
        self.contents += self.table
        self.table.clear()
        print("Clearing out the deads...")
        self.contents -= self.nextRoundRemovals
        self.nextRoundRemovals.clear()
        print("Starting a new round!")
        self.report()
        self.turnOrder.append("NEW ROUND BEGINS")
        pass

    def load(self):
        # Looks in the local folder for yaml files, lists them, attempts to load the one the user specifies.
        # Load it into a temporary holder. Check to see that it's actually a dict where each item is valid.
        # If it passes muster, display the dict nicely to the user, with colour.
        # If the user agrees that that is what they want, put it into the main bag and clear the holder.
        folderContents = self.list_files()
        print("Existing YAML files in the local folder:")
        for i, v in enumerate(folderContents):
            print("[{}] {}".format(i, v))
        selection = input("Load which file? Input only the index number.]> ")
        try:
            assert selection.isnumeric()
            with open(folderContents[int(selection)], 'r') as f:
                tempHolder = yaml.load(f, Loader=yaml.FullLoader)
            assert isinstance(tempHolder, dict)
            print("\nLoaded data:")
            if len(tempHolder) == 0:
                print("Absolutely nothing!")
            else:
                for k, v in tempHolder.items():
                    if k not in self.colour_lookup.keys():
                        self.colour_lookup[k] = self.colourise(k)
                    else:
                        pass
                    print(fg(*self.colour_lookup[k]) + "{}x {}".format(v, k) + fg.rs)
            decision = input("OK to put into the bag? y to commit.]> ").lower()
            if decision == 'y':
                self.contents += Counter(tempHolder)
                print("Loading complete!")
                self.report()
            else:
                print("Loading cancelled, returning to main menu...")
        except Exception as e:
            print("Loading failed! ", e)
        pass

    def save(self):
        # Saves the bag's contents, in DICT form, to a new YAML file which the user names.
        # If there is stuff on the table, the user is warned, and asked if they want those items included.
        # Also, the end-of-round token is NOT included in the save.
        # When a name is given, check to see if such a file already exists; if it does, ask if you want to overwrite.
        if len(self.table) > 0:
            print("There are tokens on the table:")
            for k, v in self.table.items():
                print(fg(*self.colour_lookup[k]) + "{}x {}".format(v, k) + fg.rs)
            comprehensive = input("Include those in the save? y for yes.]> ")
            if comprehensive.lower() != 'y':
                # EXCLUDE the table from the data
                saveData = dict(self.contents - Counter({"End of round": 1}))
            else:
                saveData = dict((self.contents + self.table) - Counter({"End of round": 1}))
        else:
            saveData = dict(self.contents - Counter({"End of round": 1}))
        folderContents = self.list_files()
        print("Existing YAML files in the local folder:")
        for i, v in enumerate(folderContents):
            print("[{}] {}".format(i, v))
        appellation = input("Save under what name? The .yaml suffix will be appended automatically.]> ")
        try:
            assert appellation.isalnum()  # No weird characters thanks
            assert len(appellation) > 0  # And we do need a nonzero name
            saveloc = ''.join([appellation, '.yaml'])
            if saveloc in folderContents:
                overwrite = input(
                    "WARNING! File already exists with that name! Input 'y' to overwrite.]> ").lower() == 'y'
                assert overwrite
                print("Overwriting file...")
            with open(saveloc, 'w') as f:
                yaml.dump(saveData, f)
        except Exception as e:
            print("Saving cancelled! ", e)
        return None

    def list_files(self):
        fileFilter = lambda x: (x[-5:].lower()==".yaml" or x[-4:].lower()==".yml")
        folderContents = [file for file in os.listdir(self.workingDir) if fileFilter(file)]
        return folderContents

    def turns(self):
        for i, v in enumerate(self.turnOrder):
            print("{}: {}".format(i, v))

    def extract_counter(self, command, default=2):
        # This is the single-line split-text-to-Counter parser.
        # Takes a Command (a subset of what the user typed in) which HAS been checked for basic correct structure.
        # i.e. we should already be sure that we have a LIST of STRINGS with at least ONE ELEMENT.
        # Converts that information to Counter form (following a given default for missing information) and returns it.
        # It has no comprehension of the context of what the counter will actually be used for.
        # It has no idea where the request came from; it leaves the problem of making an appropriate guess to others.
        try:
            if command[-1].isdigit():
                num_tokens = int(command.pop())  # valid command received
            else:
                num_tokens = default
            name_token = " ".join([word.capitalize() for word in command])
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
            if (clr[0] * 3 // 4 + clr[1] + clr[2] // 2) > 235:
                break
            else:
                pass
        random.setstate(randstate)
        return clr


# PROGRAM START
print("\nThis is an initiative-managing program for Troika!")
print("Troika!'s initiative system involves having a lot of tokens in a bag and drawing them out one at a time.")
print("Whoever's token gets pulled out gets to take a turn. If the End of Round token is pulled, refill the bag.")
print("Heroes get 2 tokens each. Hirelings get 1 each. Monsters range from 1 to 8.")
random.seed()
baglist = []
valid_commands = ['help', 'quit', 'add', 'remove', 'pull', 'check', 'next', 'turns', '', 'save', 'load', 'kill']

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
            b.add(c_split[1:])
        if action == 'remove':
            b.remove(c_split[1:])
        if action == 'kill':
            b.kill(c_split[1:])
        if (action == 'pull') or (action == ''):
            b.pull()
        if action == 'check':
            b.report()
        if action == 'next':
            b.next()
        if action == 'turns':
            b.turns()
        if action == 'save':
            b.save()
        if action == 'load':
            b.load()
    except Exception as e:
        print("Invalid input!" + str(e))
        print("Valid commands:", ', '.join(valid_commands))

print("Program over.")
