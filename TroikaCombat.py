# This is a tool for tracking combat initiative for the the RPG system "Troika!"

# A description of what operation looks like and what the program is internally doing.
# User (the GM) starts the program by dragging the PC list onto it.
#   That's just a list of names and initiative counts each (often 2), separated by commas.
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

# WARNING: RAMBLE ZONE

# Dragging files is a neat trick but Pycharm doesn't play nice with it; I'll do something else entirely.
# But I definitely want to have a method of loading things from file fast!
# Therefore I need to make decisions on what EXACTLY these saved-files actually contain.
# There's no point pretending that a file of "Dragon 8" is user-friendly if it's just as finicky as any alternatives.
# An actual YAML structure that straight-up describes the actual dicts you want is just fine.
# That's also easier to extend later if I want my save-files to cover extra stuff like colours or kill-amounts.

# I've got FOUR WAYS that a token may get into the bag.
# 1. The user types it in; "add bob the spider 8". The instruction is broken up, checked for validity, and used.
# 2. The special "End of Round" token added at the beginning. A hard-coded special case of the manual input.
# 3. Loading formatted data from a YAML file. Very little overlap with the 2nd way.
# 4. Adding tokens currently on the table back into the bag. Not a source of NEW tokens.

# The more I look at this the more I feel like the load-from-file method has very little overlap with the manual add.
# Therefore, they should remain entirely separate methods.
# Also, I can't load crap until I have a file to load from, so I'll start with the functions for SAVING those.

# Todo:
# Todo: the kill method. You bank removals for later. Any ideas for ease for tokens/enemy?
# Todo: Make it so that the load() function doesn't replicate code from other functions e.g. colouring and report.

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
                print("{}: {}".format(k, v))

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
        try:
            if c_split[-1].isnumeric():  # Remember the last element is taken as a QUANTITY if it is numeric
                assert len(c_split) > 1  # Ensure we'll still have something usable as a name after removing that
            else:
                assert len(c_split) > 0  # We must have a nonzero amount of instruction to act on
            order = self.extract_counter(c_split, default=1000)
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

    def load(self):
        # Looks in the local folder for yaml files, lists them, attempts to load the one the user specifies.
        # Load it into a temporary holder. Check to see that it's actually a dict where each item is valid.
        # If it passes muster, display the dict nicely to the user, with colour.
        # If the user agrees that that is what they want, put it into the main bag and clear the holder.
        folderContents = self.list_files()
        print("Existing YAML files in the local folder:")
        for i, v in enumerate(folderContents):
            print("[{}] {}".format(i, v))
        selection = input("Load which file? Input only the index number.")
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
random.seed()
baglist = []
valid_commands = ['help', 'quit', 'add', 'remove', 'pull', 'check', 'next', 'turns', '', 'save', 'load']

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
