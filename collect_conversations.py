'''
Collect all of your Facebook conversations, ever. 

Usage: python collect_conversations.py <username> <password> <your_facebook_id> <friend_file> <output_dir> 

You can find your Facebook ID by digging in the HTML. 
This script will store each conversation in a .txt file 
named after your friend's username, in the provided 
output directory. This script also takes as input a tab- 
delimited file containing your friends' user ids, names, 
and usernames. You can manually compile this or generate it 
using the get_friends.py script. 
'''

import re
import os
import sys
import json
import urllib
import requests
import operator
from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup as bs

try:
	username = sys.argv[1]
	password = sys.argv[2]
	my_id = sys.argv[3]
	friend_file_path = sys.argv[4]
	output_dir = sys.argv[5]
except IndexError:
	print "Usage: python collect_conversations.py <username> <password> <your_facebook_id> <friend_file> <output_dir>"
	sys.exit(1)

# Specifies the maximum number of messages that are stored in a single request's
# response JSON, 5000 is a safe value (breaks at higher values)
json_limit = 5000

# Facebook urls
base_url = "https://www.facebook.com/"
login_url = "https://www.facebook.com/login.php?login_attempt=1"

# Regex for extracting the fb_dtsg token from your facebook home page (after login)
dtsg_str = '<input type=\"hidden\" name=\"fb_dtsg\" value=\"(.*)\" autocomplete=\"off\" />'

# POST headers sent with both the login and the message history requests
headers = {'Host': 'www.facebook.com',
		   'Origin':'http://www.facebook.com',
		   'Referer':'http://www.facebook.com/',
		   'User-Agent': '"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36'
		   }

# The basic skeleton of the ajax request facebook uses to get more messages between you and a friend
def friend_url(my_id, friend_id, json_limit, offset, fb_dtsg):
	return 'https://www.facebook.com/ajax/mercury/thread_info.php?&messages[user_ids][%d][limit]=%d&messages[user_ids][%d][offset]=%d&client=web_messenger&__user=%d&__a=1&fb_dtsg=%s' % (friend_id, json_limit, friend_id, offset, my_id, fb_dtsg)	

# The basic skeleton of the ajax request facebook uses to get more messages from a group thread 
def thread_url(my_id, friend_id, json_limit, offset, fb_dtsg):
	return 'https://www.facebook.com/ajax/mercury/thread_info.php?&messages[thread_fbids][%d][limit]=%d&messages[thread_fbids][%d][offset]=%d&client=web_messenger&__user=%d&__a=1&fb_dtsg=%s' % (friend_id, json_limit, friend_id, offset, my_id, fb_dtsg)


def login(session, username, password):
	# Open the Facebook login page in the session
	home_request = session.get(base_url).text
	# Load the login page into a BeautifulSoup soup object 
	login_soup = bs(home_request, "html5lib")
	# Extract the LSD token from Facebook login page, required for login post request
	lsd = str(login_soup.find_all('input', attrs={"name": "lsd"})[0]['value'])
	# Login data for the Login POST request
	login_data = {
	    'locale': 'en_US',
	    'non_com_login': '',
	    'email': username,
	    'pass': password,
	    'lsd': lsd
	}
	# Log in and store the response page (your Facebook home feed)
	content = session.post(login_url, data=login_data, verify=False)
	return content 

def get_message_history(session, fb_dtsg, my_id, friend_id, username, thread=False):

	offset = 0
	num_messages = 0

	# Will store history for this friend in its own file 
	output = open(os.join(output_dir, username + '.txt'), 'w')

	while True:
			
		# Create the ajax url 
		if thread:
			url = thread_url(my_id, friend_id, json_limit, offset, fb_dtsg)
		else:
			url = friend_url(my_id, friend_id, json_limit, offset, fb_dtsg)

		# Run the GET request and store the response data (JSON of message history)
		data = session.get(url, headers=headers, verify=False).text
		# Remove some leading characters 
		data = data[9:]
		# Convert JSON response to Python dict 
		message_dict = json.loads(data)

		try:
			message_list = message_dict['payload']['actions']
		except KeyError:
			print 'Error:::No payload or actions in message dict, make sure you have correct log in information/user id'
			break

		num_messages += len(message_list)

		for message in message_list:

			# Message text 
			try:
				message_content = message['body'].replace('\t', ' ').replace('\n', ' ')
			except KeyError:
				# This occurs when people name threads 
				message_content = message['log_message_body'].replace('\t', ' ').replace('\n', ' ')

			# When the message was sent 
			sent = str(message['timestamp'])

			# Type of device from which message was sent 
			source = ' '.join(message['source_tags'])
			if 'mobile' in source:
				source = 'mobile'
			else:
				source = 'chat'

			# Who sent the message 
			author = int(message['author'].split(':')[1])
			if author == my_id:
				sender = 'me'
			else:
				sender = str(friend_id)

			#attachments = message['attachments']

			# Location data, if possible 
			if message['coordinates'] is not None:
				lat = message['coordinates']['latitude']
				lng = message['coordinates']['longitude']
				coords = str(lat) + ',' + str(lng)
			else:
				coords = 'None,None'

			out = [sender, message_content.encode('utf8'), source, sent, coords]

			# Additional group thread stuff 
			if thread:
				try:
					chat_name = message['log_message_data']['name']
				except KeyError:
					chat_name = ''
				out.append(chat_name)

			output.write('\t'.join(out) + '\n')


		if len(message_list) < json_limit:
			print '\t', num_messages, 'with', username
			break
		else:
			offset += json_limit 

	output.close()
	return num_messages

# To log in to facebook, start a session 
session = requests.Session()
content = login(session, username, password)
try:
	# If the dtsg token is in the html of the page, you've successfully logged in 
	fb_dtsg = re.search(dtsg_str, content.content).group(1).split('\"')[0]
	print "Logged in!"
except:
	# Otherwise, something went wrong and you're most likely back at the log in 
	# page - make sure you have the correct login credentials and user id 
	print "Unable to log in... :("
	sys.exit(1)

# Collect messages for each id in friend file 
friend_file = open(friend_file_path).read().splitlines()
for line in friend_file:
	uid, name, username = line.split('\t')
	try:
		uid = int(uid)
	except ValueError:
		print 'Found group thread:'
		if 'conversation' in line:
			convo_id = line.split('conversation-')[1]
			if '.' in convo_id:
				convo_id = convo_id.split('.')[1]
			print 'Getting message history for group thread:', convo_id 
			convo_name = 'conversation-' + convo_id
			num_messages = get_message_history(session, fb_dtsg, my_id, int(convo_id), convo_name, thread=True)
			print num_messages, 'with', convo_name 
		else:
			print 'Word conversation not in name...'
		continue


	print 'Getting message history for:', line  
	num_messages = get_message_history(session, fb_dtsg, my_id, uid, username)
	print num_messages, 'with', name 

# Now have fun analyzing your results! 
