from urllib.parse import urlparse
from urllib.parse import parse_qs
from tqdm import tqdm
import requests
import datetime
import argparse
import logging
import math
import re
import os

def verbose():
	try:
		import http.client as http_client
	except ImportError:
		# Python 2
		import httplib as http_client
	http_client.HTTPConnection.debuglevel = 1

	# You must initialize logging, otherwise you'll not see debug output.
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

	#requests.get('https://httpbin.org/headers')
#verbose()

HELP = '''
>>>> HELP MENU <<<<

Utilizzo: unitelmaDownloader.py [-h] -u USERNAME -p PASSWORD [-f FILE] [-v] [-l LINK] [-a] [-o] [-F FILTER FILTER] [-g] [-n FILENAME]

Argomenti:
    -h,           --help               : Mostra questa schermata di aiuto ed esce
  * -u USERNAME,  --username USERNAME  : Username per loggarti dentro unitelma
  * -p PASSWORD,  --password PASSWORD  : Password per loggarti dentro unitelma
    -f FILE,      --file     FILE      : File da cui leggere, linea per linea, l'elenco di video da scaricare
    -c COMMAND    --command  COMMAND   : Comando da eseguire a fine download
    -v,           --verbose            : Imposta la modalità verbosa. Due livelli possibili
Per ogni linea di --file oppure direttamente da linea di comando (Se si vuole scaricare un solo video) è possibile specificare questi argomenti:
(NOTA: Devi selezionare almeno un video da scaricare, tra gli argomenti e --file!)
  * -l LINK,      --link     LINK          : Link del video da scaricare
    -g,           --getInfo            : Ottiene le informazioni sulle stream del video al posto di scaricarlo
    -n FILENAME,  --fileName FILENAME  : Nome del file in output
    -a,           --modeAnd            : I filtri per la scelta della stream da scaricare sono in AND (default)
    -o,           --modeOr             : I filtri per la scelta della stream da scaricare sono in OR
    -F KEY REGEX, --filter   KEY REGEX : Specifica un filtro sul campo KEY delle stream, che deve matchare la REGEX
* argomenti obbligatori

Campi KEY possibili delle stream:
    internalId      : Numero in ordine della stream
    width           : Larghezza del video
    height          : Altezza del video
    bitrate         : Bitrate del video
    bitrateStr      : Bitrate del video come formattato in --getInfo
    framerate       : Framerate del video
    flavorId        : Utilizzato da unitelma per la selezione della qualità del video
    entryId         : Utilizzato da unitelma per l'identificazione del video
    size            : Dimensione del video
    sizeStr         : Dimensione del video come formattata in --getInfo
    duration        : Durata in secondi del video
    durationStr     : Durata del video come formattata in --getInfo   
    name            : Nome del video
    description     : Descrizione del video
    searchText      : Utilizzato da unitelma per l'indexing del video
    tags            : Tag utilizzati da unitelma del video
    tagsStr         : Tags formattati come in --getInfo
(NOTA: Se non è stato possibile selezionare una stream coi parametri specificati, verrà visualizzato --getInfo per tale link)

UnitelmaDownloader creato da https://stranck.ovh
'''

VERBOSE = False
#USERNAME = ""
#PASSWORD = ""

#COURSE_ID = 0 #1888
#VIDEO_LINK = "" #"https://elearning.unitelma.it/mod/kalvidres/view.php?id=50969"

session = requests.Session()

def convert_size(size_bytes):
	if size_bytes == 0:
		return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return "%s%s" % (s, size_name[i])

def printStream(stream, videoLink):
	durationStr = "Time: " + stream["durationStr"]
	dimensionStr = "Size: " + stream["sizeStr"]
	qualityStr = f"Quality: {stream['width']}x{stream['height']} @ {stream['framerate']}fps"
	bitrateStr = f"Bitrate: " + stream["bitrateStr"]

	tagsStr = stream["tagsStr"]

	nameStr			= stream["name"] 		if (len(stream["name"]) < 148) 			else stream["name"][:144] 			+ "..."
	descriptionStr	= stream["description"] if (len(stream["description"]) < 141) 	else stream["description"][:137] 	+ "..."
	searchTxtStr	= stream["searchText"] 	if (len(stream["searchText"]) < 141)	else stream["searchText"][:137] 	+ "..."
	tagsStr			= tagsStr			 	if (len(tagsStr) < 150)					else tagsStr[:146] 					+ "..."

	s  = "+--- Stream ID: " + (str(stream["internalId"]) + " ").ljust(4, "-") + "--- Video link: " + (videoLink + " ").ljust(123, "-") + "+\n"
	s += "|  " + (durationStr.ljust(30) + dimensionStr.ljust(30) + qualityStr.ljust(30) + bitrateStr.ljust(30)).ljust(156) + 	"|\n"
	s += "|  " + ("Name: \"" 			+ nameStr + "\"")			.ljust(156) +												"|\n"
	s += "|  " + ("Description: \"" 	+ descriptionStr + "\"")	.ljust(156) +												"|\n"
	s += "|  " + ("Search text: \"" 	+ searchTxtStr + "\"")		.ljust(156) +												"|\n"
	s += "|  " + ("Tags: " 				+ tagsStr)					.ljust(156) +												"|\n"
	s += "+" + "".ljust(158, "-") 																							  + "+"
	print(s)

def selectStream(streams, params):
	for stream in streams:
		modeAnd = params["modeAnd"]
		found = modeAnd
		for key, value in params["filters"].items():
			x = re.search(value, str(stream[key]))
			if(modeAnd):
				found = found and (x != None)
			else:
				found = found or (x != None)
		if(found):
			return stream
	return None

def analyzeParam(args):
	link = args.link[0] if args.link is not None else None
	#courseid = -1
	modeAnd = not args.modeOr
	getInfo = args.getInfo
	filters = {}
	fileName = args.fileName[0] if args.fileName is not None else None
	if fileName is not None and not fileName.endswith(".mp4"):
		fileName += ".mp4"
	if(args.filter is not None):
		for f in args.filter:
			key = f[0]
			value = f[1]
			filters[key] = value
	'''
	i = 1
	while(i < len(args)):
		arg = args[i].lower()
		if(arg == "--link"):
			i += 1
			link = args[i]
		#elif(arg == "--courseid"):
		#	i += 1
		#	courseid = int(args[i].strip())
		elif(arg == "--modeAnd"):
			modeAnd = True
		elif(arg == "--modeOr"):
			modeAnd = False
		elif(arg == "--filter"):
			i += 1
			key = args[i]
			i += 1
			value = args[i]
			filters[key] = value
		elif(arg == "--getInfo"):
			getInfo = True
		elif(arg == "--fileName"):
			i += 1
			fileName = args[i]
		
		i += 1'''
	if(len(filters) == 0):
		getInfo = True
	obj = {
		"link": link,
		#"courseId": courseid,
		"modeAnd": modeAnd,
		"filters": filters,
		"getInfo": getInfo,
		"fileName": fileName
	}
	return None if (link == None) else obj

def analyzeArgs():
	global VERBOSE
	usr = None
	pw = None
	cmd = None
	params = []
	verboseLevel = 0

	parser = argparse.ArgumentParser("UnitelmaDownloader - Scarica lezioni da Unitelma - Creato da https://stranck.ovh", add_help=False)
	parser.add_argument('-u', '--username', nargs=1, required=True)
	parser.add_argument('-p', '--password', nargs=1, required=True)
	parser.add_argument('-f', '--file', nargs=1, default=None)
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('-c', '--command', nargs=1, default=None)
	parser.add_argument('-h', '--help', action='store_true')

	parser.add_argument('-l', '--link', nargs=1)
	parser.add_argument('-a', '--modeAnd', action='store_true')
	parser.add_argument('-o', '--modeOr', action='store_true')
	parser.add_argument('-F', '--filter', nargs=2, action='append')
	parser.add_argument('-g', '--getInfo', action='store_true')
	parser.add_argument('-n', '--fileName', nargs=1)


	args = parser.parse_args()
	if(args.help):
		print(HELP)
		exit(1)
	usr = args.username[0] if args.username is not None else None
	pw = args.password[0] if args.password is not None else None
	cmd = args.command[0] if args.command is not None else None
	if(args.file is not None):
		fileName = args.file[0]
		with open(fileName) as file:
			n = 0
			for line in file:
				line = line.strip()
				sp = line.split()
				param = analyzeParam(sp)
				if(param == None):
					print(f"*** AN ERROR OCCURRED LOADING PARAM AT LINE {n}")
				else:
					params.append(param)
				n += 1
	verboseLevel = args.verbose
	if(verboseLevel > 0):
		VERBOSE = True
	if(verboseLevel > 1):
		verbose()

	'''i = 1
	#TODO permit classic arg passing like -vv, or -uUSERNAME
	while(i < len(args)):
		arg = args[i].lower()
		if(arg == "--help"):
			print(HELP)
			exit(1)
		elif(arg == "--username" or arg == "-u"):
			i += 1
			usr = args[i]
		elif(arg == "--password" or arg == "-p"):
			i += 1
			pw = args[i]
		elif(arg == "--file" or arg == "-f"):
			i += 1
			fileName = args[i]
			with open(fileName) as file:
				n = 0
				for line in file:
					line = line.strip()
					sp = line.split()
					param = analyzeParam(sp)
					if(param == None):
						print(f"*** AN ERROR OCCURRED LOADING PARAM AT LINE {n}")
					else:
						params.append(param)
					n += 1
		elif(arg == "--verbose" or arg == "-v"):
			if(verboseLevel == 0):
				VERBOSE = True
				verboseLevel += 1
			elif(verboseLevel == 1):
				verbose()
				verboseLevel += 1
		#else:
		#	print(f"Unrecognized argoument: {arg}\n\n")
		#	print(HELP)
		#	exit(1)
		
		i += 1'''

	param = analyzeParam(args)
	if(param != None):
		params.append(param)

	if(usr == None or pw == None or len(params) == 0):
		print(HELP)
		exit(1)
	return usr, pw, params, cmd


def login(session, usr, pw):
	try: 
		#print(usr, pw)
		if VERBOSE:
			print("Logging in...", end="")
		'''
		curl 'https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2' \
	-H 'Connection: keep-alive' \
	-H 'Pragma: no-cache' \
	-H 'Cache-Control: no-cache' \
	-H 'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"' \
	-H 'sec-ch-ua-mobile: ?0' \
	-H 'sec-ch-ua-platform: "Windows"' \
	-H 'Upgrade-Insecure-Requests: 1' \
	-H 'Origin: https://idp.unitelma.it' \
	-H 'Content-Type: application/x-www-form-urlencoded' \
	-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36' \
	-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
	-H 'Sec-Fetch-Site: same-origin' \
	-H 'Sec-Fetch-Mode: navigate' \
	-H 'Sec-Fetch-User: ?1' \
	-H 'Sec-Fetch-Dest: document' \
	-H 'Referer: https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2' \
	-H 'Accept-Language: en-US,en;q=0.9' \
	-H 'Cookie: JSESSIONID=B860612B6E5BEF8046F6BADBB0A23CC1.idp-unitelma.prod-idpbe141' \
	--data-raw 'j_username=corso.informatica&j_password=informatica&_eventId_proceed=' \
	--compressed
		'''
		
		#params = {
		#	"j_username": USERNAME,
		#	"j_password": PASSWORD,
		#	"_eventId_proceed": ""
		#}
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			#"Origin": "https://idp.unitelma.it"
		}
		#print("\n\n#1 =========================================================\n")
		r = session.get("https://elearning.unitelma.it/", headers=heahder)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			"Referer": "https://elearning.unitelma.it/unitelma_login.php"
		}
		#print("\n\n#2 =========================================================\n")
		r = session.get("https://elearning.unitelma.it/auth/shibboleth/index.php?", headers=heahder)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			"Referer": "https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s1",
			"Origin": "https://idp.unitelma.it"
		}
		params = {
			"shib_idp_ls_exception.shib_idp_session_ss": "",
			"shib_idp_ls_success.shib_idp_session_ss": "true",
			"shib_idp_ls_value.shib_idp_session_ss": "",
			"shib_idp_ls_exception.shib_idp_persistent_ss": "",
			"shib_idp_ls_success.shib_idp_persistent_ss": "true",
			"shib_idp_ls_value.shib_idp_persistent_ss": "",
			"shib_idp_ls_supported": "true",
			"_eventId_proceed": ""
		}
		#print("\n\n#3 =========================================================\n")
		r = session.post("https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s1", headers=heahder, data=params)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			"Referer": "https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s1"
		}
		#print("\n\n#4 =========================================================\n")
		#r = session.post("https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2", headers=heahder, data=params)
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			"Origin": "https://idp.unitelma.it",
			"Referer": "https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2"
		}
		params = {
			"j_username": usr,
			"j_password": pw,
			"_eventId_proceed": ""
		}
		#print("\n\n#5 =========================================================\n")
		r = session.post("https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2", data=params, headers=heahder)
		if(VERBOSE):
			print(".", end="")
		#r = session.get("https://elearning.unitelma.it/")
		t = r.text
		relayState = "cookie:" + t.split('"RelayState" value="cookie&#x3a;')[1].split('"/>')[0]
		resp = t.split('"SAMLResponse" value="')[1].split('"/>')[0]
		heahder = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
			"Origin": "https://idp.unitelma.it",
			"Referer": "https://idp.unitelma.it/"
		}
		params = {
			"RelayState": relayState,
			"SAMLResponse": resp
		}
		r = session.post("https://elearning.unitelma.it/Shibboleth.sso/SAML2/POST", data=params, headers=heahder, allow_redirects=True)
		#print(r.text)
		if("Non sei collegato" in r.text):
			if(VERBOSE):
				print(" ", end="")
			print("LOGIN FAILED (1)")
			exit(1)
		if(VERBOSE):
			print(" Done!")
	except Exception as e:
		#print(e)
		if(VERBOSE):
			print(" ", end="")
		print("LOGIN FAILED (2)")
		exit(1)
	
def getMainID(session, videoLink):
	if(VERBOSE):
		print("Getting main ID...", end=" ")
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
		"Referer": videoLink
	}
	r = session.get(videoLink, headers=headers)
	t = r.text
	#print(t)
	id = t.split('src="https://elearning.unitelma.it/mod/kalvidres/lti_launch.php?')[1].split("entryid%2F")[1].split("%")[0]
	courseId = t.split("https://elearning.unitelma.it/course/view.php?id=")[1].split("\"")[0]
	if(VERBOSE):
		print(id)
	return id, courseId

def getKs(session, videoLink, mainId, courseId):
	#proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
	if(VERBOSE):
		print("Obtaining kaf endpoint...", end=" ")
	'''curl 'https://elearning.unitelma.it/mod/kalvidres/lti_launch.php?courseid=1888&height=602&width=658&withblocks=0&source=http%3A%2F%2Fkaltura-kaf-uri.com%2Fbrowseandembed%2Findex%2Fmedia%2Fentryid%2F0_hbyn9aso%2FshowDescription%2Ffalse%2FshowTitle%2Ftrue%2FshowTags%2Ffalse%2FshowDuration%2Ffalse%2FshowOwner%2Ftrue%2FshowUploadDate%2Ffalse%2FembedType%2FoldEmbed%2FplayerSize%2F602x658%2FplayerSkin%2F23448850%2FcrsId%2F1888%2FcmId%2F50969%2F' \
  -H 'Connection: keep-alive' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  -H 'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-Dest: iframe' \
  -H 'Referer: https://elearning.unitelma.it/mod/kalvidres/view.php?id=50969' \
  -H 'Accept-Language: en-US,en;q=0.9,it-IT;q=0.8,it;q=0.7' \
  -H 'Cookie: _shibstate_1638816139_e539=https%3A%2F%2Felearning.unitelma.it%2Fauth%2Fshibboleth%2Findex.php%3F; _shibsession_6c6561726e2d756e6974656c6d612d70726f6468747470733a2f2f73702d656c6561726e696e672d756e6974656c6d612d70726f642e63696e6563612e69742f73686962626f6c657468=_d528ef80609f967d643794a770004d1f; MoodleSessiontelmaprod=f73c41c107452d55c566374ed47e6fba' \
  --compressed'''
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
		"Referer": videoLink
	}
	link = f'https://elearning.unitelma.it/mod/kalvidres/lti_launch.php?courseid={courseId}&height=602&width=658&withblocks=0&source=http%3A%2F%2Fkaltura-kaf-uri.com%2Fbrowseandembed%2Findex%2Fmedia%2Fentryid%2F{mainId}%2FshowDescription%2Ffalse%2FshowTitle%2Ftrue%2FshowTags%2Ffalse%2FshowDuration%2Ffalse%2FshowOwner%2Ftrue%2FshowUploadDate%2Ffalse%2FembedType%2FoldEmbed%2FplayerSize%2F602x658%2FplayerSkin%2F23448850%2FcrsId%2F1888%2FcmId%2F50969%2F'
	r = session.get(link, headers=headers)
	t = r.text
	#endpoint = "https://" + t.split('<form action="https://')[1].split("/")[0] + "/"
	kafRefer = t.split('<form action="')[1].split('"')[0]
	if(VERBOSE):
		print(kafRefer)

	if(VERBOSE):
		print("Validating js...", end=" ")
	lines = t.split("\n")[1:]
	params = {}
	for line in lines:
		if "</form>" in line:
			break
		name = line.split('name="')[1].split('"')[0].replace("&amp;", "&")
		value = line.split('value="')[1].split('"')[0].replace("&amp;", "&")
		params[name] = value

	#print(params)
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
		"Referer": "https://elearning.unitelma.it/"
	}
	r = session.post(kafRefer, headers=headers, data=params)
	t = r.text
	#print(t)
	#print(kafRefer)
	#print(t)
	lnk = t.split("window.location.href = '")[1].split("'")[0]
	if(VERBOSE):
		print("Done!")

	if(VERBOSE):
		print("Obtaining ks token...", end=" ")
	'''curl 'https://kaf-113prod.elearning.unitelma.it/browseandembed/index/media-redirect/entryid/0_hbyn9aso/showDescription/false/showTitle/true/showTags/false/showDuration/false/showOwner/true/showUploadDate/false/embedType/oldEmbed/playerSize/602x658/playerSkin/23448850/crsId/1888/cmId/50969/thumbEmbed//autoPlay//startTime//endTime/' \
  -H 'authority: kaf-113prod.elearning.unitelma.it' \
  -H 'pragma: no-cache' \
  -H 'cache-control: no-cache' \
  -H 'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-dest: iframe' \
  -H 'referer: https://kaf-113prod.elearning.unitelma.it/browseandembed/index/media/entryid/0_hbyn9aso/showDescription/false/showTitle/true/showTags/false/showDuration/false/showOwner/true/showUploadDate/false/embedType/oldEmbed/playerSize/602x658/playerSkin/23448850/crsId/1888/cmId/50969' \
  -H 'accept-language: en-US,en;q=0.9,it-IT;q=0.8,it;q=0.7' \
  -H 'cookie: kms-locale=custom_it; kms_ctamuls=pdc7j7shjp32piovlkg1nkum14' \
  --compressed'''
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
		"Referer": kafRefer
	}
	#lnk = kafEndpoint + f'/browseandembed/index/media-redirect/entryid/{mainId}/showDescription/false/showTitle/true/showTags/false/showDuration/false/showOwner/true/showUploadDate/false/embedType/oldEmbed/playerSize/602x658/playerSkin/23448850/crsId/{courseId}/cmId/50969/thumbEmbed//autoPlay//startTime//endTime/'
	#lnk = kafRefer.replace("/media/", "/media-redirect/") + "/thumbEmbed//autoPlay//startTime//endTime/"
	#print()
	#print(lnk)
	#print(kafRefer)
	r = session.get(lnk, headers=headers)
	t = r.text
	#print(t)
	ks = t.split('{"ks":"')[1].split('"')[0]
	if(VERBOSE):
		print(ks)
	return ks

def getStreams(session, mainId, ksToken):
	if(VERBOSE):
		print("Asking for streams metadata...", end=" ")
	'''curl -i -X POST \
   -H "Content-Type:application/x-www-form-urlencoded" \
   -d "apiVersion=3.1" \
   -d "expiry=86400" \
   -d "clientTag=kwidget%3Av2.81.4" \
   -d "1:ks=djJ8MTEzfD_Ht59bsunOL8vuaAP8tORMEabxKc258eyF_YvqCwKHM69hFCjOrXwfmyrVp2ShjAFFJVINd_Bz0CQmB8SaU70KTchB0oaEwztB-YEyR15675mxu9QubYthzU95-9wBJtv8g07TJDuB2rPY0f2VHwlmCj__MNTzOVcZl5RXR16PMr4mNj3NVS8r5PhMj8AcMlIrzhGJe4WU03vhXeyo_xPjxC_8LRjHQGZvxOcAIV3zotX1IYEyhndnteivbR3oKsxS9vW-gAJSxOXAjVLJzwooOAb67ytNkaTM3bi9U2UzEvoH5FoIYpBa4_aO_aGnNNz6dEDrcyphEEDq6wTxBFVVxqP3UCkl0fDYeGBj48Ts4N7cR52JWzNmDu0f3epK6TuV1ATdQG0NKXil6F8Uu9D5Cf0nRoZwh5B41q6AUhAcICbhyQnQxhMTApj52UCCw7BcHnQ34B89JyjqyZYta3LcrF1yEw2fljd2Q7Xgip13" \
   -d "1:service=baseEntry" \
   -d "1:action=list" \
   -d "1:filter:objectType=KalturaBaseEntryFilter" \
   -d "1:filter:typeEqual=1" \
   -d "1:filter:parentEntryIdEqual=0_hbyn9aso" \
   -d "format=1" \
   -d "2:ks=djJ8MTEzfD_Ht59bsunOL8vuaAP8tORMEabxKc258eyF_YvqCwKHM69hFCjOrXwfmyrVp2ShjAFFJVINd_Bz0CQmB8SaU70KTchB0oaEwztB-YEyR15675mxu9QubYthzU95-9wBJtv8g07TJDuB2rPY0f2VHwlmCj__MNTzOVcZl5RXR16PMr4mNj3NVS8r5PhMj8AcMlIrzhGJe4WU03vhXeyo_xPjxC_8LRjHQGZvxOcAIV3zotX1IYEyhndnteivbR3oKsxS9vW-gAJSxOXAjVLJzwooOAb67ytNkaTM3bi9U2UzEvoH5FoIYpBa4_aO_aGnNNz6dEDrcyphEEDq6wTxBFVVxqP3UCkl0fDYeGBj48Ts4N7cR52JWzNmDu0f3epK6TuV1ATdQG0NKXil6F8Uu9D5Cf0nRoZwh5B41q6AUhAcICbhyQnQxhMTApj52UCCw7BcHnQ34B89JyjqyZYta3LcrF1yEw2fljd2Q7Xgip13" \
   -d "2:service=flavorAsset" \
   -d "2:action=list" \
   -d "2:filter:entryIdEqual={1:result:objects:0:id}" \
   -d "3:ks=djJ8MTEzfD_Ht59bsunOL8vuaAP8tORMEabxKc258eyF_YvqCwKHM69hFCjOrXwfmyrVp2ShjAFFJVINd_Bz0CQmB8SaU70KTchB0oaEwztB-YEyR15675mxu9QubYthzU95-9wBJtv8g07TJDuB2rPY0f2VHwlmCj__MNTzOVcZl5RXR16PMr4mNj3NVS8r5PhMj8AcMlIrzhGJe4WU03vhXeyo_xPjxC_8LRjHQGZvxOcAIV3zotX1IYEyhndnteivbR3oKsxS9vW-gAJSxOXAjVLJzwooOAb67ytNkaTM3bi9U2UzEvoH5FoIYpBa4_aO_aGnNNz6dEDrcyphEEDq6wTxBFVVxqP3UCkl0fDYeGBj48Ts4N7cR52JWzNmDu0f3epK6TuV1ATdQG0NKXil6F8Uu9D5Cf0nRoZwh5B41q6AUhAcICbhyQnQxhMTApj52UCCw7BcHnQ34B89JyjqyZYta3LcrF1yEw2fljd2Q7Xgip13" \
   -d "3:service=flavorAsset" \
   -d "3:action=list" \
   -d "3:filter:entryIdEqual={1:result:objects:1:id}" \
   -d "4:ks=djJ8MTEzfD_Ht59bsunOL8vuaAP8tORMEabxKc258eyF_YvqCwKHM69hFCjOrXwfmyrVp2ShjAFFJVINd_Bz0CQmB8SaU70KTchB0oaEwztB-YEyR15675mxu9QubYthzU95-9wBJtv8g07TJDuB2rPY0f2VHwlmCj__MNTzOVcZl5RXR16PMr4mNj3NVS8r5PhMj8AcMlIrzhGJe4WU03vhXeyo_xPjxC_8LRjHQGZvxOcAIV3zotX1IYEyhndnteivbR3oKsxS9vW-gAJSxOXAjVLJzwooOAb67ytNkaTM3bi9U2UzEvoH5FoIYpBa4_aO_aGnNNz6dEDrcyphEEDq6wTxBFVVxqP3UCkl0fDYeGBj48Ts4N7cR52JWzNmDu0f3epK6TuV1ATdQG0NKXil6F8Uu9D5Cf0nRoZwh5B41q6AUhAcICbhyQnQxhMTApj52UCCw7BcHnQ34B89JyjqyZYta3LcrF1yEw2fljd2Q7Xgip13" \
   -d "4:service=flavorAsset" \
   -d "4:action=list" \
   -d "4:filter:entryIdEqual={1:result:objects:0:parentEntryId}" \
 "https://kmc.l2l.cineca.it/api_v3/index.php?service=multirequest"'''
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
		"Referer": "https://kaf-113prod.elearning.unitelma.it/",
		"origin": "https://kaf-113prod.elearning.unitelma.it",
		"authority": "kmc.l2l.cineca.it"
	}
	params = {
		"apiVersion": "3.1",
		"expiry": "86400",
		"clientTag": "kwidget:v2.81.4",
		"format": "1",
		"ignoreNull": "1",
		"action": "null",
		"1:ks": ksToken,
		"1:service": "baseEntry",
		"1:action": "list",
		"1:filter:objectType": "KalturaBaseEntryFilter",
		"1:filter:typeEqual": "1",
		"1:filter:parentEntryIdEqual": mainId,
		"2:ks": ksToken,
		"2:service": "flavorAsset",
		"2:action": "list",
		"2:filter:entryIdEqual": "{1:result:objects:0:id}",
		"3:ks": ksToken,
		"3:service": "flavorAsset",
		"3:action": "list",
		"3:filter:entryIdEqual": "{1:result:objects:1:id}",
		"4:ks": ksToken,
		"4:service": "flavorAsset",
		"4:action": "list",
		"4:filter:entryIdEqual": "{1:result:objects:0:parentEntryId}"
	}
	r = session.post("https://kmc.l2l.cineca.it/api_v3/index.php?service=multirequest", headers=headers, data=params)
	j = r.json()
	allMetaData = j[0]["objects"]
	j = j[1:]
	streams = []
	i = 0
	for stream in j:
		#print(stream)
		highRes = stream["objects"][0]
		tags = set()

		obj = {
			"internalId": i,
			"width": highRes["width"],
			"height": highRes["height"],
			"bitrate": highRes["bitrate"],
			"framerate": highRes["frameRate"],
			"flavorId": highRes["id"],
			"entryId": highRes["entryId"],
			"size": highRes["size"],

			"duration": 0,
			"name": "-",
			"description": "-",
			"searchText": "-",

			"durationStr": str(datetime.timedelta(seconds=0)),
			"bitrateStr": f"{convert_size(highRes['bitrate'])}ps",
			"sizeStr": convert_size(highRes["size"])
		}

		temp = highRes["tags"]
		temp = temp.split(",")
		for t in temp:
			tags.add(t.strip())
		
		if(i < len(allMetaData)):
			metaData = allMetaData[i]
			obj["duration"] = metaData["duration"]
			obj["name"] = metaData["name"]
			obj["description"] = metaData["description"]
			obj["searchText"] = metaData["searchText"]

			obj["durationStr"] = str(datetime.timedelta(seconds=metaData["duration"]))

			temp = metaData["tags"]
			temp = temp.split(",")
			for t in temp:
				tags.add(t.strip())

		obj["tags"] = tags
		obj["tagsStr"] = ", ".join(tags)

		streams.append(obj)
		i += 1
	if(VERBOSE):
		print("Done!")
	return streams

def getDownloadLink(stream):
	return f"https://streaming.l2l.cineca.it/p/113/sp/11300/serveFlavor/entryId/{stream['entryId']}/v/2/flavorId/{stream['flavorId']}/forceproxy/true/name/a.mp4"


def downloadVideo(param):
	videoLink = param["link"]
	print("\nDownloading: " + videoLink)
	#courseId = param["courseId"]
	mainId, courseId = getMainID(session, videoLink)
	ksToken = getKs(session, videoLink, mainId, courseId)
	streams = getStreams(session, mainId, ksToken)
	selectedStream = selectStream(streams, param)
	if(param["getInfo"] or selectedStream == None):
		s  = "\n"
		s += "".ljust(160, "-") + "\n"
		s += "  INFO for video: " + videoLink + "\n"
		s += "".ljust(160, "v") + "\n"
		print(s)
		for stream in streams:
			print()
			printStream(stream, videoLink)
			print()
	else:
		downloadLink = getDownloadLink(selectedStream)
		if(VERBOSE):
			print("Downloading from: " + downloadLink)
		fileName = param["fileName"]
		if(fileName == None):
			parsed_url = urlparse(videoLink)
			originalLinkId = parse_qs(parsed_url.query)['id'][0]
			fileName = selectedStream["name"] + "_" + str(courseId) + "_" + originalLinkId + ".mp4"
			fileName = re.sub(r'[^a-zA-Z0-9_\-\s\.]', '', fileName)
		if(os.path.exists(fileName)):
			print(f"Skipping '{fileName}'; already download")
		else:
			download(downloadLink, fileName)
			print(fileName + "\t downloaded!")

def download(url, fileName):
	response = requests.get(url, stream=True)
	total_size_in_bytes= int(response.headers.get('content-length', 0))
	block_size = 1024 #1 Kibibyte
	progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
	with open(fileName, 'wb') as file:
		for data in response.iter_content(block_size):
			progress_bar.update(len(data))
			file.write(data)
	progress_bar.close()
	if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
		print("ERROR, something went wrong")

if __name__ == "__main__":
	usr, pw, params, cmd = analyzeArgs()
	login(session, usr, pw)
	for param in params:
		downloadVideo(param)
	if cmd is not None:
		if(VERBOSE):
			print("Executing " + cmd)
		os.system(cmd)

#kafEndpoint, kafRefer = getKaf(session, VIDEO_LINK, mainId, COURSE_ID)
#verbose()



#printStream(streams[0], VIDEO_LINK, 0)