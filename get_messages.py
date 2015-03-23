import requests
import re
import json
import urllib
from bs4 import BeautifulSoup as bs
import sys
from collections import Counter
import operator
from datetime import datetime

FRIENDS = {'lily':1087980499, 'evan':1549988468, 'nabil':546795441, 
'amina':1651800110, 'morgane':1326450295, 'john':509242785, 'connor':698329466, 'saskia':500907680, 'carolyn':503017978, 
'brandon':595224119, 'martin':508030950, 'group':1422984669962, 'jamie':1664490365
}
#recent:root:<2b99e5a0d98b7474cd3799f6a0a7bb45@messages.facebook.com>
#recent:root:<1422984669962:0-16fdf1482b2f86fd@mail.projektitan.com>

SELF = {'jamie':1664490365, 'saskia':500907680, 'morgane':1326450295}
JSON_LIMIT = 5000
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def get_message_history(my_id, other_id, self_name):
	
	dad_counter = 0

	headers = {'Host':'www.facebook.com',
	'Origin':'http://www.facebook.com',
	'Referer':'http://www.facebook.com/',
	#'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11'}
	'User-Agent': ' "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36'}


	s = requests.Session()
	r = s.get('https://www.facebook.com/').text
	soup = bs(r, "html5lib")
	lsd = str(soup.find_all('input', attrs={"name": "lsd"})[0]['value'])


	#login_data = json.load(open('info/%s.json' % self_name, 'r'))

	login_data = {}
	login_data['email'] = 'morgane.ciot@mail.mcgill.ca'
	login_data['pass'] = 'rock3tm@n1103'
	login_data['locale'] = 'en_US'
	login_data['non_com_login'] = ''
	login_data['lsd'] = lsd

	r=s.post('https://login.facebook.com/login.php?login_attempt=1',data=login_data,verify=False)
	#print r.content
	#print r.status_code

	#r = s.get('https://www.facebook.com/').text
	soup = bs(r.content, "html5lib")
	fb_dtsg = re.search('<input type=\"hidden\" name=\"fb_dtsg\" value=\"(.*)\" autocomplete=\"off\" />' , r.content).group(1).split('\"')[0]# name="fb_dtsg">', r.content)
	#<input type="hidden" autocomplete="off" value="AQGUut9tO-jU_9w" name="fb_dtsg">
	#fb_dtsg = str(soup.find('input', attrs={"name": "fb_dtsg"}))#['value'])
	#print fb_dtsg

	#url = 'https://www.facebook.com/ajax/mercury/thread_info.php?&messages[user_ids][%d][limit]=%d&client=mercury&__user=%d&__a=1&__dyn=7nmanEyl2qm9udDgDxyIGzGpUW9ACxO4p9GgSmEVFLFwxBxCbzElx2ubhEoBBzEy78S8zU46iicyaw&__req=18&fb_dtsg=%s&ttstamp=26581706610112175988710311269977989&__rev=1609713' % (other_id,limit,my_id,fb_dtsg)
	offset = 0
	output = []
        monthly_activity = Counter()
        num_chars_me = Counter()
        num_chars_other = Counter()
	num_messages = 0
	unique_locations = set()
	while True:
		
		#url = 'https://www.facebook.com/ajax/mercury/thread_info.php?&messages[user_ids][%d][limit]=%d&messages[user_ids][%d][offset]=%d&client=web_messenger&__user=%d&__a=1&fb_dtsg=%s' % (other_id,JSON_LIMIT,other_id,offset,my_id,fb_dtsg)
		
		url = 'https://www.facebook.com/ajax/mercury/thread_info.php?&messages[thread_fbids][%d][limit]=%d&messages[thread_fbids][%d][offset]=%d&client=web_messenger&__user=%d&__a=1&fb_dtsg=%s' % (other_id,JSON_LIMIT,other_id,offset,my_id,fb_dtsg)
		print url
		
		data = s.get(url,headers=headers,verify=False).text
		data = data[9:]
		message_dict = json.loads(data)
		#dump json for decoding purposes
		#json.dump(message_dict, open('asdf.json', 'w'))
		try:
			message_list = message_dict['payload']['actions']
		except KeyError:
			print 'Num messages:', num_messages
			break
		num_messages += len(message_list)
		for m in message_list:
			message_content = m['body']

			print message_content

			#if '.pdf' in message_content:
			#	print message_content
			read = m['is_unread']
			if read == 'false':
				read = 'read'
			else:
				read = 'unread'
			timestamp = m['timestamp_datetime']
			day = m['timestamp_absolute']
			try:
				year = day.split(',')[1].strip()
				month = '%02d' % (int(MONTHS.index(day.split(' ')[0]))+1)
			except:
				dt = str(datetime.now()).split(' ')[0]
				year = dt.split('-')[0]
				try:
					month = '%02d' % (int(MONTHS.index(day.split(' ')[0]))+1)
				except:
					month = dt.split('-')[1]#MONTHS[int(dt.split('-')[1])]
			monthly_activity[year + '.' + month] += 1
			source = m['source_tags']
			if 'mobile' in source:
				source = 'mobile'
			else:
				source = 'chat'
			author = int(m['author'].split(':')[1])
			if author == my_id:
				num_chars_me[year + '.' + month] += len(message_content)
			else:
		                num_chars_other[year + '.' + month] += len(message_content)
			attachments = m['attachments']
			if m['coordinates'] is not None:
				loc = '%s, %s' % (m['coordinates']['latitude'], m['coordinates']['longitude'])
				unique_locations.add(loc)
				print '%s\t%s\t%s\t%s\n' % (m['author'], m['timestamp_absolute'], loc, message_content)
			"""
			if len(attachments) > 0:
				for att in attachments:
					att_type = att['attach_type']
					if att_type == 'sticker':
						img_url = att['url'].replace('\\/', '/')
						#img_name = att['url'].split('/')[-1]
					if att_type == 'photo':
						img_url = att['preview_url'].replace('\\/', '/')
						print img_url
					image=urllib.URLopener()
					image.retrieve(img_url,'temp.png')
					#handle_image_conversion('temp.png')
			"""
			#output.append({'content':message_content,'read':read,'timestamp':timestamp,'source':source,'author':author})
		if len(message_list) < JSON_LIMIT:
			print num_messages
			break
		else:
			offset += JSON_LIMIT
	#return url
	for uniq_loc in unique_locations:
		print uniq_loc
	return monthly_activity, num_chars_me, num_chars_other

	#return output
	#print url
if __name__=='__main__':
	if len(sys.argv) == 3:
		self_name = sys.argv[1]
		friend = sys.argv[2]
		rs, rs2, rs3 = get_message_history(SELF[self_name],FRIENDS[friend], self_name)
		sorted_rs = sorted(rs.items(), key=operator.itemgetter(0))
		# fout = open('/home/2010/jmccor6/public_html/facebook_friends/facebook_%s-%s.tsv' % (self_name,friend), 'w')
		# fout.write('date\tcount\tmychars\totherchars\n')

		# #get current month/year
		# dt = str(datetime.now()).split(' ')[0]
  #               year = int(dt.split('-')[0])
  #               month = int(dt.split('-')[1])

		# syear, smonth = sorted_rs[0][0].split('.')
		# syear = int(syear)
		# smonth = int(smonth)
		# while True:
		# 	year_month = '%d.%02d' % (syear, smonth)
		# 	fout.write('%s\t%d\t%d\t%d\n' % (year_month, rs[year_month], rs2[year_month], rs3[year_month]))
		# 	if syear == year and smonth == month:
		# 		break
		# 	smonth += 1
		# 	if smonth % 12 == 1:
		# 		syear += 1
		# 		smonth = 1
		# #for month, count in sorted_rs:
		# #	fout.write('%s\t%d\n' % (month, count))
		# fout.close()
	else:
		print 'ERROR: incorrect number of input arguments. python get_messages.py self_name friend_name'
		exit()