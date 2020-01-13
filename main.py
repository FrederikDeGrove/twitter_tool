import copy
import sys
import tweepy
import datetime
import logging
import csv
import os
import time
from pytz import timezone


class TwitterRest:

    def __init__(self, keys, egos, use_profile_data=True, use_name_id_data=False,
                 user_data_file="profile_data_" + str(datetime.datetime.now().day) + str(datetime.datetime.now().month) +
                                str(datetime.datetime.now().year), name_id_file="id_name"):

        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.user_data_file = user_data_file
        self.name_id_file = name_id_file

        if isinstance(keys, str): #if it is a string, it should be a valid location
            #read in keys
            #order in file should be: consumer key, consumer secret, access token, access token secret)
            self.keys = []
            try:
                reader = open(keys, "r")
                for line in reader:
                    self.keys.append(line.rstrip())
                reader.close()
            except IOError:
                print("problem with reading keys")

        else: #should be list with keys in the right order
            assert isinstance(keys, list), "wrong format for keys"
            self.keys = keys

        if isinstance(egos, str):
            #read in egos from location
            try:
                self.egos = []
                reader = open(egos, "r")
                for line in reader:
                    self.egos.append(line.rstrip())
                reader.close()
            except IOError:
                print("problem with reading ego file names")
                sys.exit()

        else:
            assert isinstance(egos, list), "wrong format for keys"
            self.egos = egos

        if use_profile_data:
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project data'))
                user_data = dict()
                with open(base_dir + "/" + user_data_file + ".csv", "r") as dat:
                    reader = csv.reader(dat, delimiter=';', quotechar="\'")
                    next(reader)
                    for row in reader:
                        user_data.update({row[2].lower(): row})
                self.user_objects = user_data
            except IOError:
                print("problem with reading in profile data. Probably, no valid file was found - change settting to False")
                sys.exit()
        else:
            self.user_objects = dict()

        if use_name_id_data:
            self.id_name = dict()
            # should make sure this code does not overwrite the id_name file or object when it is first loaded
            # same goes for the user_object
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project data'))
                id_to_name = dict()
                with open(base_dir + "/" + name_id_file + ".csv", "r") as dat:
                    reader = csv.reader(dat, delimiter=';', quotechar="\'")
                    next(reader)
                    for row in reader:
                        id_to_name.update({row[0]: row[1]})
                self.id_name = {**self.id_name, **id_to_name} #this gives access to a self.id_name object which is a dict with
                # the keys being the IDs AS A STRING and the names of the profiles as the values

            except IOError:
                print("problem with reading in id_name data")
        else:
            self.id_name = dict()

        self.api = self.authenticate()
        self.logger = logging.getLogger('twitter')


    def authenticate(self):
        auth = tweepy.OAuthHandler(self.keys[0], self.keys[1])
        auth.set_access_token(self.keys[2], self.keys[3])
        return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=100, retry_delay=10,
                          retry_errors=(401, 404, 500, 503, 104))


    def profile_information_search(self, names, write=True, filename=None, type="screennames"):

        if filename == None:
            filename = self.user_data_file  #name given during init(ialization)

        if self.user_objects: #if the init has a user object loaded from a text file, we already have them
            #so no need to look em up
            if type == "screennames":
                names = [i.lower() for i in names]
                existing_names = set(self.user_objects.keys())
                new_names = set(names).difference(existing_names)
                names = new_names
            elif type =="user_id":
                names = [str(name) for name in names]
                existing_names = set([str(val[0]) for val in self.user_objects.values()])
                new_names = set(names).difference(existing_names)
                names = new_names

        for name in names:
            try:
                user = self.api.get_user(name)
                protected_status = 0
                print(("fetching user data of {0} started at {1}").format(name, datetime.datetime.now(tz=timezone('Europe/Amsterdam')).time()))
                if user.protected:
                    # remove users with a protected account
                    #self.logger.debug("Removing user {0} because of protected account".format(name))
                    #self.egos.remove(name)
                    protected_status = 1


                self.user_objects.update({user.screen_name.lower():
                    [
                    user.id,
                    user.name,
                    user.screen_name,
                    user.friends_count,
                    user.followers_count,
                    user.description,
                    user.created_at,
                    user.url,
                    user.profile_image_url,
                    user.lang,
                    user.location,
                    user.verified,
                    datetime.datetime.now().date(),
                    protected_status
                    ]
                                          })
                self.id_name.update({user.id: user.screen_name.lower()})
                    # time.sleep(5)
                ### IF ANY PROBLEM PERSISTENTLY APPEARS HERE IN TERMS OF RATE LIMIT AND CRASHES
                ### THEN WE WILL HAVE TO USE THE WRITE_PROFILE_INFORMATION AND ID_NAME FUNCTIONS IN THIS LOOP
                ### NOW WE FIRST COLLECT ALL NAMES BEFORE WRITING THEM TO OUR FILE
            except tweepy.TweepError:
                self.logger.debug("Error in profile_information_search: error get username EGO-user")

        if write and names:
            self.write_profile_information(self.user_objects)
            self.write_name_ID(self.id_name) #also write ID and name to id_name file
        return self.user_objects
        #return self.id_name # dit kan helemaal niet, een return na een return TO CHECK


    def write_profile_information(self, user_object, filename=None):

        if filename == None:
            filename = self.user_data_file

        if os.path.exists(self.base_dir + "/project data/" + filename + ".csv"):
            append_write = 'a'  # append if already exists

            #check which names are already in there so no double writing is done
            file_csv = open(self.base_dir + "/project data/"+ filename + ".csv", "r")
            reader = csv.reader(file_csv, delimiter=';', quotechar="\'")
            existing_names = set()
            for row in reader:
                existing_names.add(row[2].lower())
        else:
            append_write = 'w'  # make a new file if not
            existing_names = set()

        with open(self.base_dir + "/project data/"+ filename + ".csv", append_write) as myfile:
            writer = csv.writer(myfile, delimiter=';', quotechar="\'")
            if append_write != 'a':
                writer.writerow(["user_id", "name", "screen_name", "friends_count", "followers_count", "user_description",
                                 "date_created", "url", "profile_image_url", "language", "location",
                                 "verified", "date_collected", "protected_status"])
            for name in user_object:
                if name.lower() not in existing_names:
                    user = user_object.get(name)
                    writer.writerow(user)


    def ID_to_name(self, ids, write=True): #input is ids, output screennames (and updated user_object file)
        assert len(ids) > 0, "your ids object cannot be empty"
        assert all([isinstance(id, str) for id in ids]), "ids should be in string format"
        ids = set(ids)
        #why do we take the next step, it's not because it is in de user_objects object that it is in the id_name object, is it?
        #and is the goal of this function not to do just that. IF it is in the user object, you can read name and id from there
        #still to do
        #ids_in_objects = set(str(value[0]) for value in self.user_objects.values()) #get the ID values in the stored in the objects object
        #new_ids = list(ids.difference(ids_in_objects))
        #new_ids = [str(i) for i in new_ids] #this step should be redundant since you check already with the assert if it's strings
        new_ids = ids
        if self.id_name:
            other_id = self.id_name.keys() #check which ids are already in the id_name object
            temp = set(new_ids).difference(set(other_id))
            new_ids = list(temp)
        #so now we excluded those IDs that are in the ID_name file but we also have to check whether we have those
        #IDs in the user_object. If they are there, we can use that information to write to the
        if self.user_objects:
            #we make a dict with ids as keys and screennames as values from the self.user_objects
            user_ids_in_user_objects = dict(zip([values[0] for values in self.user_objects.values()], [keys for keys in self.user_objects.keys()]))
            #now if any of the ids in the new_ids list is in the user_ids_in_users_objects, we have to use that data to write it
            #away and then remove it from new_ids.
            id_name_to_write = dict()
            for key, value in user_ids_in_user_objects.items():
                if key in new_ids:
                    id_name_to_write[key] = value
                    new_ids.remove(key)
            self.write_name_ID(id_name_to_write)

        #print("total number of names is {}").format(len(new_ids))
        for i in range(0,len(new_ids),100):
            print("converting batch", i)
            try:
                cont = True #added to check if dat is not empty
                if len(new_ids) > 1:
                    dat = self.api.lookup_users(user_ids= new_ids[i:i+100])
                    print("sleeping 3 minutes before getting the next batch ID_Name converts")
                    time.sleep(180)
                else:
                    try:
                        dat = [self.api.get_user(new_ids[0])]
                    except tweepy.TweepError:
                        print("there was a problem with the ID_name conversion of one user", new_ids[0])
                        pass
                try: #added, check if this works if user is suspended
                    for user in dat:
                        protected_status = 1 if user.protected else 0
                        #since we are getting this information anyway, we use it to add to the existing
                        #user_objects file

                        if user.screen_name:
                            self.user_objects.update({user.screen_name.lower():
                                [
                                    user.id,
                                    user.name,
                                    user.screen_name,
                                    user.friends_count,
                                    user.followers_count,
                                    user.description,
                                    user.created_at,
                                    user.url,
                                    user.profile_image_url,
                                    user.lang,
                                    user.location,
                                    user.verified,
                                    datetime.datetime.now().date(),
                                    protected_status
                                ]
                            })
                            if not self.id_name.get(str(user.id)):
                                #if the user is not in the id_user object, add him/her
                                self.id_name.update({str(user.id): user.screen_name.lower()})
                except UnboundLocalError:
                    print("user probably suspended")
                    cont = False
                    pass
            except tweepy.TweepError:
                print("there was a problem with the ID_name conversion (line 260, see user ", user)
                pass

            if write and cont:
                self.write_name_ID(self.id_name)
                self.write_profile_information(self.user_objects)


    def write_name_ID(self, name_id_dict, filename=None): #function to write the pair id and name to the csv file
        #name_id_dict is a dict which you get from the ID_to_name function (you get self.id_name

        if filename == None:
            filename = self.name_id_file

        if os.path.exists(self.base_dir + "/project data/" + filename + ".csv"):
            append_write = 'a'  # append if already exists
            #check which IDs are already in there so no double writing is done
            file_csv = open(self.base_dir + "/project data/"+ filename + ".csv", "r")
            reader = csv.reader(file_csv, delimiter=';', quotechar="\'") #if a file already exists, read in the id_name combinations that are
            #already available so no double work is done.
            existing_ids = set()
            for row in reader:
                existing_ids.add(str(row[0]))
        else:
            append_write = 'w'  # make a new file if not
            existing_ids = set()

        with open(self.base_dir + "/project data/"+ filename + ".csv", append_write) as myfile:
            writer = csv.writer(myfile, delimiter=';', quotechar="\'")
            if append_write != 'a': #if it is a new file, add a header
                writer.writerow(["user_id", "screen_name"])
            for key, value in self.id_name.items(): #now cycle through the name_id_dict file to add all combinations
                if str(key) not in existing_ids:
                    writer.writerow([key, value])


    def extract_profiles_from_master(self, names, name_object="branch_objects", write=True):
        assert isinstance(names, list), "input of names should be a list of names"
        newObjects = dict()
        names_in_user_object = self.user_objects.keys() #we need to check if those profiles are already in our file
        #so let's read them out first. If they are not, they need to be added with the profile_information_search function
        for name in names:
            if name not in names_in_user_object:
                print(name) #debug info
                print("this user was not found, check your code around line 260")
                #sys.exit()
                self.profile_information_search([name], write=True) #problem here is what happens with protected or deleted accounts
                #this should be caught before you come here
            newObjects.update({name : self.user_objects.get(name)})
        if write:
            self.write_profile_information(newObjects, filename=name_object)
        return newObjects

    def collect_networks(self, file_name): #use this if you want to use an existing network file
        #it will read in the data in dict format (from: to)
        #important, the network file NEEDS TO HAVE A HEADING
        print("make sure your network file has headers!!!!")
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project data'))
            network = dict()
            with open(base_dir + "/" + file_name + ".csv", "r") as dat:
                reader = csv.reader(dat, delimiter=';', quotechar="\'")
                next(reader)
                for row in reader:
                    if network.get(row[0]):
                        network[row[0]].append(row[1])
                    else:
                        network.update({row[0]:[row[1]]})
            return network
        except IOError:
            print("no network file found - exiting program")
            sys.exit()

    def check_user_protected_in_attrs(self, ids):
        print("WARNING: input should be IDs in list format when using the check_user_protected function")
        ids = [str(id) for id in ids]
        ids = set(ids)
        dat = dict(zip([str(i[0]) for i in self.user_objects.values()], [int(i[13]) for i in self.user_objects.values()])) #get all id / protected / name combinations
        protected_users = []
        for id in ids:
            if dat.get(id) == 1:
                protected_users.append(str(id))
        #if len(protected_users) > 0:
        #    print("the following ids are protected {}".format(protected_users))
        usebale_users = ids.difference(set(protected_users))
        return((list(usebale_users), protected_users))

    def create_network(self, egos, followers=True, following=False, full_ego=False, use_names = False, write=True):

        #if you want names, first check if the names or ids are in the user_object file, if not, add them
        if use_names:
            self.profile_information_search(egos, write=True)
            print("WARNING: using named network might take a lot more time to convert ids to names")

        # check kind of input from egos and link to use_names
        if all([element.isdigit() for ego in egos for element in ego]):
            assert not all([element.isdigit() for ego in egos for element in ego]) and \
                   isinstance(egos, list), "input must be either list with only names or list with only ID numbers"
        else:
            name_id = dict(zip(self.id_name.values(), self.id_name.keys()))
            temp_egos = [name_id.get(name.lower()) for name in egos] #extract the IDs from the user_objects file based on the names
            egos = temp_egos #these are IDs, even if you start out with names

        ### now we need to check if there are protected accounts or otherwise troublesome ones
        checked_users = self.check_user_protected_in_attrs(egos)
        egos = checked_users[0]
        print("these users are proteced and will be removed: {}".format(checked_users[1]))
        ### from here, you only work with those egos that were not protected.

        #because of troubels and errors with fetching followers and following
        # we first make an empty list where we will store the names that were collected succesfully
        # as such, we can continue where we left. We do this for followers as well as following (cf infra)
        #so we also need to read in some code where we know the succesful followers and remove them from the list
        #that needs to be collected.
        if followers:
            ## control mechanism
            #check if success_followers file exists, if so, read in the names
            successes = set()
            if os.path.isfile(self.base_dir + "/project data/"+ "succesful_followers" + ".csv"):
                reader = csv.reader(open(self.base_dir + "/project data/"+ "succesful_followers" + ".csv", "r"), delimiter=';', quotechar="\'")
                for row in reader:
                    successes.add(row[0])

            # now start building networks
            follower_NW = dict()
            egos_followers = copy.deepcopy(egos)

            #remove those egos that are in the success file
            egos_followers = [i for i in set(egos_followers).difference(successes)]

            for name in egos_followers: #now collect followers for each name still in ego_followers
                allFollowers = [i for i in tweepy.Cursor(self.api.followers_ids, name).pages()]
                allFollowers = [id for sublist in allFollowers for id in sublist]
                if len(allFollowers) > 0:
                    follower_NW.update({name: allFollowers})
                self.write_network(follower_NW, append_to_existing=True,file_name="temp_NW_file_followers")  # write away network before anything crashes
                #write name to file with success
                if os.path.isfile(self.base_dir + "/project data/" + "succesful_followers" + ".csv"):
                    append_write = 'a'
                else:
                    append_write = 'w'

                with open(self.base_dir + "/project data/" + "succesful_followers" + ".csv", append_write) as myfile:
                    writer = csv.writer(myfile, delimiter=';', quotechar="\'")
                    writer.writerow([name])

                print("sleeping for three minutes before collecting the next batch followers for {}".format(name))
                time.sleep(180)
            self.follower_NW = follower_NW
            if use_names:
                self.follower_NW_named = self.convert_NW_names(follower_NW)
            if write:
                self.write_network(follower_NW, file_name="follower_NW")
                if use_names:
                    self.write_network(self.follower_NW_named, file_name="follower_NW_named")

        if following: #or full_ego:

            ## control mechanism
            # check if success_following file exists, if so, read in the names
            successes = set()
            if os.path.isfile(self.base_dir + "/project data/" + "succesful_following" + ".csv"):
                reader = csv.reader(open(self.base_dir + "/project data/" + "succesful_following" + ".csv", "r"),
                                    delimiter=';', quotechar="\'")
                for row in reader:
                    successes.add(row[0])

            # now start building networks
            following_NW = dict()
            egos_following = copy.deepcopy(egos)
            # remove those egos that are in the success file
            egos_following = [i for i in set(egos_following).difference(successes)]

            for name in egos_following:
                allFollowing = [i for i in tweepy.Cursor(self.api.friends_ids, name).pages()]
                allFollowing = [id for sublist in allFollowing for id in sublist]

                if len(allFollowing) > 0:
                    following_NW.update({name: allFollowing})
                self.write_network(following_NW, append_to_existing=True,file_name="temp_NW_file_following")  # write away network before anything crashes
                #write name to file with success
                if os.path.isfile(self.base_dir + "/project data/" + "succesful_following" + ".csv"):
                    append_write = 'a'
                else:
                    append_write = 'w'

                with open(self.base_dir + "/project data/" + "succesful_following" + ".csv", append_write) as myfile:
                    writer = csv.writer(myfile, delimiter=';', quotechar="\'")
                    writer.writerow([name])

                #following_NW.update({name: allFollowing})
                #self.write_network(following_NW) #write away network before anything crashes
                print("sleeping for 3 minutes before collecting the next batch following for {}".format(name))
                time.sleep(180)
            self.following_NW = following_NW


            if use_names:
                self.following_NW_named = self.convert_NW_names(following_NW)

            if write:
                self.write_network(following_NW, file_name="following_NW")
                if use_names:
                    self.write_network(self.following_NW_named, file_name="following_NW_named")

        if full_ego:
            self.create_ego_network(follower_NW, filename="full_ego") if followers else self.create_ego_network(following_NW, filename="full_ego")
            if use_names:
                self.create_ego_network(self.follower_NW_named, filename="full_ego_named") if followers else self.create_ego_network(self.following_NW_named, filename="full_ego_named")


    def create_ego_network(self,network, filename = "ego_NW"):
        #this function always writes away the network
        #network should be a network as created by the function collect_networks
        full_ego_NW = dict()
        egos_full = [key for key in network.keys()]
        for ego in egos_full:
            full_ego_NW.update({ego: []})
        for ego in egos_full:
            alters = set([str(i) for i in network[ego]])
            intersect = alters.intersection(set(egos_full))
            full_ego_NW[ego] = list(intersect)
        self.full_ego_NW = full_ego_NW
        self.write_network(full_ego_NW, file_name= filename)


    def convert_NW_names(self, IDs_NW_dict):
        # this function first collects all IDs from a given network (in dict format)
        # then it checks to what extent these IDs already exists in order to make a
        # new set of IDs that need to be converted.
        names = [name for names_ in IDs_NW_dict.values() for name in names_]
        self.profile_information_search(names, write=True, type="user_id")

        ids = []
        for key, value in IDs_NW_dict.items():
            ids.append(str(key))
            for name in value:
                ids.append(str(name))
        ids = set(ids)
        control_list = set(self.id_name.keys())
        to_fetch = ids.difference(control_list)
        if len(to_fetch) >0:
            self.ID_to_name(to_fetch, write = True) #this is necessary because a name/id can be in user_object file while not begin in ID_to_name


        NW_named = dict()
        for key, value in IDs_NW_dict.items():
            names = []
            for id_ in value:
                names.append(self.id_name.get(str(id_)))
            try:
                key_name = self.id_name.get(key)
                if key_name:
                    NW_named.update({key_name: names})
                else:
                    NW_named.update({key: names})
            except tweepy.TweepError:
                pass
                # NW_named.update({key:names})

        return NW_named


    def write_network(self, network, file_name="NW_file", attributes=False, append_to_existing=False):
        if append_to_existing:
            try:
                append_write = 'a'  # append if already exists
                #check which IDs are already in there so no double writing is done
                #still to do, but his is not the way, here you only read in the existing network and replace it with the new one....
                '''
                file_csv = open(self.base_dir + "/project data/"+ file_name + ".csv", "r")
                reader = csv.reader(file_csv, delimiter=';', quotechar="\'")
                existing_network = dict()
                for row in reader:
                    if existing_network.get(row[0]):
                        existing_network[row[0]].append(row[1])
                    else:
                        existing_network.update({row[0]:[row[1]]})
                network = existing_network
                '''
            except IOError:
                print("no existing network - making new network")
                append_write = 'w'

        else:
            append_write = 'w'  # make a new file if not


        #network has a dict structure
        source = []
        target = []
        for key, value in network.items():
            if value:
                source.extend([key] * len(value))
                target.extend(value)
            else:
                source.extend([key])
                target.extend([None])
        dat = list(zip(source, target))

        with open(self.base_dir + "/project data/"+ file_name + ".csv", append_write) as myfile:
            writer = csv.writer(myfile, delimiter=';', quotechar="\'")
            if append_write == "w": #we don't need this anymore since we always delete it if it exists in a previous file
                writer.writerow(["source", "target"])
            for row in dat:
                writer.writerow(row)
        if attributes:
            names = []
            for key, value in network.items():
                names.append(key.lower())
                if value:
                    for alter in value:
                        if alter:
#hier is er nog een probleem als value None is.... zou nu normaal opgelost moeten zijn met lijn erboven
                            names.append(alter.lower())
            names = set(names)
            names = list(names)
            self.extract_profiles_from_master(names, write=True, name_object= file_name + "_attr")
        self.write_name_ID(self.id_name) #dit mss aan of uit laten zeggen gezien dit problemen oplevert als profiel protected is EN
        # het meer tijd kost... zeker al sje gewoon netwerk vanuit de timelines wil opmaken is dit niet nodig TODO


    def create_bimodal(self, egos, network, counts=True, threshold=2, write=False, file_name="bimodal", write_attrs=False):
    # the threshold function determines the minimum number of links before being included
    # the write_attrs makes a separate file for the people included in the bimodal network (to check)
        bimodalCounts = dict()
        for names in network.values():
            for name in names:
                if bimodalCounts.get(name):
                    bimodalCounts[name] += 1
                else:
                    bimodalCounts.update({name: 1})

        bimodal = dict()
        for name in egos:
            bimodal.update({name:[]})

        for name in egos:
            for key, value in bimodalCounts.items():
                if key in network.get(name.lower()) and value >= threshold:
                    bimodal[name].append(key)
        self.bimodal = bimodal
        if counts:
            self.bimodalCounts = bimodalCounts

        if write:
            self.write_network(bimodal, file_name)

        if write_attrs:
            names = set(egos)
            for values in bimodal.values():
                for value in values:
                    names.add(value)
            self.extract_profiles_from_master(list(names), file_name + "attrs")

    def timeline(self, egos, write=True, file_name="Egotimeline", write_networks=False, use_RT = False):
        #the use_RT only refers to the hashtag/mentions/replies/urls networks. If False, it does not take these objects
        #into account if it deals with retweets; If true, you get all these objects also from tweets that are retweets
        #the timeline file will always have both tweets and retweets but with a variable indicating which is which
        self.EgoTimeLine = []
        for user in egos:
            print(("getting timeline for user {0}").format(user))
            dat = [i for i in tweepy.Cursor(self.api.user_timeline, user, tweet_mode="extended").pages()]
            dat = [i for sublist in dat for i in sublist]
            self.EgoTimeLine.append(dat)
            time.sleep(180)
        if write:
            if use_RT:
                self.writeTimelines(file_name=file_name, write_networks=write_networks,include_RT_in_NWs=True)
            else:
                self.writeTimelines(file_name=file_name, write_networks=write_networks, include_RT_in_NWs=False)

    def writeTimelines(self, file_name="EgoTimeline", write_networks=False, include_RT_in_NWs=False):
        self.timeline_hashtags = dict()
        self.timeline_mentions = dict()
        self.timeline_replies = dict()
        self.timeline_urls = dict()
        # author.id, author.screen_name,  text, id, retweeted, source, coordinates, in_reply_to_user_id
        # entities : hashtags (list met daarin dict key = 'text'),
        # user_mentions (list met daarin dict key = 'screen_name',
        # urls: list met daarin dict key = 'expanded_url'
        # truncated, source_url, favorite_count, retweet_count

        self.timeline_data = dict()
        BASEdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        with open(BASEdir + "/project data/" + file_name + ".csv", "w") as myfile:
            writer = csv.writer(myfile, delimiter=';', quotechar="\'")
            writer.writerow(["date", "time", "user_id", "screen_name", "text", "isRetweet" , "tweet_id", "source", "in_reply_to_user_id",
                             "hashtags", "user_mentions", "urls", "truncated", "source_url", "#favorites", "#retweets"])
            for tweets in self.EgoTimeLine:
                for tweet in tweets:

                    hashtags = [ha.get('text') for ha in [hash for hash in tweet.entities.get('hashtags')]],
                    flat_hash = []
                    for item in hashtags:
                        for el in item:
                            flat_hash.append(el)

                    user_mentions = [ha.get("screen_name") for ha in [hash for hash in tweet.entities.get('user_mentions')]],
                    flat_mentions = []
                    for item in user_mentions:
                        for el in item:
                            flat_mentions.append(el)

                    urls = [ha.get("expanded_url") for ha in [hash for hash in tweet.entities.get('urls')]],
                    flat_url = []
                    for item in urls:
                        for el in item:
                            flat_url.append(el)

                    line = [tweet.created_at.date(),
                            tweet.created_at.time(),
                            tweet.author.id,
                            tweet.author.screen_name,
                            tweet.full_text,
                            "RT" if "RT" in tweet.full_text[0:2] else "NO_RT",
                            tweet.id,
                            tweet.source,
                            tweet.in_reply_to_user_id,
                            flat_hash,
                            flat_mentions,
                            flat_url,
                            tweet.truncated, tweet.source_url, tweet.favorite_count, tweet.retweet_count]
                    writer.writerow(line)

                    if include_RT_in_NWs == True or (include_RT_in_NWs == False and "RT" not in tweet.full_text[0:2]):
                        if tweet.in_reply_to_user_id:
                            #lookup name in name_id
                            str_name = self.id_name.get(str(tweet.in_reply_to_user_id))
                            #print(str_name)
                            if str_name is None:
                                print(tweet.in_reply_to_user_id)
                                self.ID_to_name([str(tweet.in_reply_to_user_id)], write=True)
                                str_name = self.id_name.get(str(tweet.in_reply_to_user_id))
                        if self.timeline_replies.get(tweet.author.screen_name):
                            if tweet.in_reply_to_user_id:
                                self.timeline_replies[tweet.author.screen_name].append(str_name)
                                #self.timeline_replies[tweet.author.screen_name].append(tweet.in_reply_to_user_id)
                        else:
                            if tweet.in_reply_to_user_id:
                                self.timeline_replies.update({tweet.author.screen_name: [str_name]})
                                #self.timeline_replies.update({tweet.author.screen_name: [tweet.in_reply_to_user_id]})


                        if self.timeline_hashtags.get(tweet.author.screen_name):
                            for hash in flat_hash:
                                self.timeline_hashtags[tweet.author.screen_name].append(hash)
                        else:
                            for i in range(len(flat_hash)):
                                if i == 0:
                                    self.timeline_hashtags.update({tweet.author.screen_name: [flat_hash[0]]})
                                else:
                                    self.timeline_hashtags[tweet.author.screen_name].append(flat_hash[i])


                        if self.timeline_mentions.get(tweet.author.screen_name):
                            for mention in flat_mentions:
                                self.timeline_mentions[tweet.author.screen_name].append(mention)
                        else:
                            for i in range(len(flat_mentions)):
                                if i == 0:
                                    self.timeline_mentions.update({tweet.author.screen_name: [flat_mentions[0]]})
                                else:
                                    self.timeline_mentions[tweet.author.screen_name].append(flat_mentions[i])


                        if self.timeline_urls.get(tweet.author.screen_name):
                            for url in flat_url:
                                self.timeline_urls[tweet.author.screen_name].append(url)
                        else:
                            for i in range(len(flat_url)):
                                if i == 0:
                                    self.timeline_urls.update({tweet.author.screen_name: [flat_url[0]]})
                                else:
                                    self.timeline_urls[tweet.author.screen_name].append(flat_url[i])


        if write_networks:
            self.write_network(self.timeline_replies, file_name="repliesNetwork")
            self.write_network(self.timeline_hashtags, file_name="hashtagsNetwork")
            self.write_network(self.timeline_mentions, file_name="mentionsNetwork")
            self.write_network(self.timeline_urls, file_name="urlsNetwork")

    def create_adjacency_matrix(self, network, write=True, filename="adjacency"):
        #at the moment,this only works for full ego networks!!!
        #at the moment, no col and row names are added, this is problematic
        #takes a network format file (dict format) and outputs an adjacency matrix
        row_names = list(network.keys())
        col_names = list(network.keys())
        #create n * m matrix and fill with 0
        adjacency = [[0 for i in range(len(row_names))] for k in range(len(row_names))]
        for key,values in network.items():
            for value in values:
                adjacency[row_names.index(key)][col_names.index(value)] = 1

        if write:
            with open(self.base_dir + "/project data/" + filename + ".csv", "w") as myfile:
                writer = csv.writer(myfile, delimiter=';', quotechar="\'")
                for row in adjacency:
                    writer.writerow(row)

    def create_full_network(self, NW_following, NW_followers, write=True, file_name="full_network", include_ego=False):
        #TODO
        print("todo")

# some examples to run

# Give name of the input file for the egos and give relevant directory
# name_input_file = "twitter_handles.csv"
# name_input_file = "namen_annaS.csv"
# twitterDIR = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'twitter'))

# make an instance reading out relevant information such as keys,
# egos from input file and if applicable id_name file and user_objects
# profiles = TwitterRest(twitterDIR + "/input files/keys.txt", twitterDIR +"/input files/" + name_input_file,
                       #use_name_id_data=True, use_profile_data=False)

# look for profiles in input file, if they don't already exist, write them away
# profiles.profile_information_search(profiles.egos,write=True)

# collect timelines, save with current date and create networks for hyperlinks, mentions, etc
# profiles.timeline(profiles.egos, write=True, write_networks=False, use_RT=False, file_name="timeline_" +
    # str(datetime.datetime.now().day) +
    # str(datetime.datetime.now().month) +
    # str(datetime.datetime.now().year))



# create networks based on followers or following and/or create a full ego network
# profiles.create_network(profiles.egos,followers=True, following=True, full_ego=True, write=True, use_names=True)

# Create bimodal network for following and followers.
# Threshold refers to the number of people egos need AT LEAST to have in common before
# being added to the network.
# profiles.create_bimodal(profiles.egos, profiles.following_NW_named, write=True,threshold=2,
#                     file_name="bimodal_thres2_followings",write_attrs=False)
# profiles.create_bimodal(profiles.egos, profiles.follower_NW_named, write=True,threshold=2,
#                     file_name="bimodal_thres2_followers",write_attrs=False)

# create named network from temp file after crashing
# profiles.write_network(profiles.convert_NW_names(
# profiles.collect_networks("temp_NW_file_following")), file_name="test_NW_File_named")
# profiles.create_ego_network(profiles.collect_networks("temp_NW_file_following"))
# profiles.create_adjacency_matrix(profiles.collect_networks("full_ego_follower"), filename="adjacency_follower")
