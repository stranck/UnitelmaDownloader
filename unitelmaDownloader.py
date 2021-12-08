from urllib.parse import urlparse
from urllib.parse import parse_qs
from tqdm import tqdm
import requests
import datetime
import argparse
import logging
import random
import math
import re
import os

def verbose():
	try:
		import http.client as http_client
	except ImportError:
		pass
	http_client.HTTPConnection.debuglevel = 1

	# You must initialize logging, otherwise you'll not see debug output.
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

HELP = '''
>>>> HELP MENU <<<<

Utilizzo: unitelmaDownloader.py -u USERNAME -p PASSWORD [-f FILE] [-v] [-c COMMAND] [-h] [-U USERAGENT] [-l LINK] [-a] [-o] [-F FILTER FILTER] [-i] [-n FILENAME] [-r]

Argomenti:
    -h,           --help                 : Mostra questa schermata di aiuto ed esce
  * -u USERNAME,  --username USERNAME    : Username per loggarti dentro unitelma
  * -p PASSWORD,  --password PASSWORD    : Password per loggarti dentro unitelma
    -f FILE,      --file     FILE        : File da cui leggere, linea per linea, l'elenco di video da scaricare
	-U USER_AGENT --userAgent USER_AGENT : UserAgent da usare nelle richieste. Default: casuale
    -c COMMAND    --command  COMMAND     : Comando da eseguire a fine download
    -v,           --verbose              : Imposta la modalità verbosa. Due livelli possibili
Per ogni linea di --file oppure direttamente da linea di comando (Se si vuole scaricare un solo video) è possibile specificare questi argomenti:
(NOTA: Devi selezionare almeno un video da scaricare, tra gli argomenti e --file!)
  * -l LINK,      --link     LINK        : Link del video da scaricare
    -i,           --getInfo              : Ottiene le informazioni sulle stream del video al posto di scaricarlo
    -n FILENAME,  --fileName FILENAME    : Nome del file in output
    -r,	          --redownload           : Riscarica un file, anche se già esiste
    -a,           --modeAnd              : I filtri per la scelta della stream da scaricare sono in AND (default)
    -o,           --modeOr               : I filtri per la scelta della stream da scaricare sono in OR
    -F KEY REGEX, --filter   KEY REGEX   : Specifica un filtro sul campo KEY delle stream, che deve matchare la REGEX
* argomenti obbligatori

Campi KEY possibili delle stream:
    internalId      : Numero in ordine della stream
    qualityId       : Id della qualità di un determinato video (0 = qualità più alta)
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

USER_AGENTS = [ #List obtained from https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
	"Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
	"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
]

USER_AGENT = random.choice(USER_AGENTS)
VERBOSE = False
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
	qualityIdStr = f"Quality ID {stream['qualityId']}"

	tagsStr = stream["tagsStr"]

	nameStr			= stream["name"] 		if (len(stream["name"]) < 148) 			else stream["name"][:144] 			+ "..."
	descriptionStr	= stream["description"] if (len(stream["description"]) < 141) 	else stream["description"][:137] 	+ "..."
	searchTxtStr	= stream["searchText"] 	if (len(stream["searchText"]) < 141)	else stream["searchText"][:137] 	+ "..."
	tagsStr			= tagsStr			 	if (len(tagsStr) < 150)					else tagsStr[:146] 					+ "..."

	s  = "+--- Internal stream ID: " + (str(stream["internalId"]) + " ").ljust(4, "-") + "--- Video link: " + (videoLink + " ").ljust(114, "-") + "+\n"
	s += "|  " + (durationStr.ljust(30) + dimensionStr.ljust(30) + qualityStr.ljust(30) + bitrateStr.ljust(30) + qualityIdStr.ljust(30)).ljust(156) + 	"|\n"
	s += "|  " + ("Name: \"" 			+ nameStr + "\"")			.ljust(156) +												"|\n"
	s += "|  " + ("Description: \"" 	+ descriptionStr + "\"")	.ljust(156) +												"|\n"
	s += "|  " + ("Search text: \"" 	+ searchTxtStr + "\"")		.ljust(156) +												"|\n"
	s += "|  " + ("Tags: " 				+ tagsStr)					.ljust(156) +												"|\n"
	s += "+" + "".ljust(158, "-") 																							  + "+"
	if(VERBOSE):
		s += "\n" + str(stream)
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

	if(len(filters) == 0):
		getInfo = True
	obj = {
		"link": link,
		"modeAnd": modeAnd,
		"filters": filters,
		"getInfo": getInfo,
		"fileName": fileName,
		"redownload": args.redownload
	}
	return None if (link == None) else obj

def analyzeArgs():
	global VERBOSE
	global USER_AGENT
	usr = None
	pw = None
	cmd = None
	params = []
	verboseLevel = 0

	parser = argparse.ArgumentParser("UnitelmaDownloader - Scarica lezioni da Unitelma - Creato da https://stranck.ovh ", add_help=False)
	parser.add_argument('-u', '--username', nargs=1)
	parser.add_argument('-p', '--password', nargs=1)
	parser.add_argument('-f', '--file', nargs=1, default=None)
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('-c', '--command', nargs=1, default=None)
	parser.add_argument('-h', '--help', action='store_true')
	parser.add_argument('-U', '--userAgent', nargs=1, default=None)

	parser.add_argument('-l', '--link', nargs=1)
	parser.add_argument('-a', '--modeAnd', action='store_true')
	parser.add_argument('-o', '--modeOr', action='store_true')
	parser.add_argument('-F', '--filter', nargs=2, action='append')
	parser.add_argument('-i', '--getInfo', action='store_true')
	parser.add_argument('-n', '--fileName', nargs=1)
	parser.add_argument('-r', '--redownload', action='store_true')


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
				sp = re.compile(r"\s(?=([^\"]*\"[^\"]*\")*[^\"]*$)").split(line) #Don't ask me how I wrote this regex. I don't remember neither
				newArgs = []
				j = 0
				while(j < len(sp)): #Shitty workaround bc I don't know how regex works in python. Hopefully this works always
					if((sp[j].startswith("'") or sp[j].startswith('"')) and sp[j][0] == sp[j][-1] and (len(sp[j]) > 2 and sp[j][-2] != '\\')):
						sp[j] = sp[j][1:-1] #Remove start and end quotes if present, the param is specified between quotes
					newArgs.append(sp[j])
					j += 2
				param = analyzeParam(parser.parse_args(newArgs))
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
	if(args.userAgent is not None):
		USER_AGENT = args.userAgent

	param = analyzeParam(args)
	if(param != None):
		params.append(param)

	if(usr == None or pw == None or len(params) == 0):
		print(HELP)
		exit(1)
	return usr, pw, params, cmd


def login(session, usr, pw):
	try: 
		if VERBOSE:
			print("Logging in...", end="")

		heahder = {
			"User-Agent": USER_AGENT,
		}
		r = session.get("https://elearning.unitelma.it/", headers=heahder)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": USER_AGENT,
			"Referer": "https://elearning.unitelma.it/unitelma_login.php"
		}
		r = session.get("https://elearning.unitelma.it/auth/shibboleth/index.php?", headers=heahder)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": USER_AGENT,
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
		r = session.post("https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s1", headers=heahder, data=params)
		if(VERBOSE):
			print(".", end="")
		heahder = {
			"User-Agent": USER_AGENT,
			"Origin": "https://idp.unitelma.it",
			"Referer": "https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2"
		}
		params = {
			"j_username": usr,
			"j_password": pw,
			"_eventId_proceed": ""
		}
		r = session.post("https://idp.unitelma.it/idp/profile/SAML2/Redirect/SSO?execution=e1s2", data=params, headers=heahder)
		if(VERBOSE):
			print(".", end="")
		t = r.text
		relayState = "cookie:" + t.split('"RelayState" value="cookie&#x3a;')[1].split('"/>')[0]
		resp = t.split('"SAMLResponse" value="')[1].split('"/>')[0]
		heahder = {
			"User-Agent": USER_AGENT,
			"Origin": "https://idp.unitelma.it",
			"Referer": "https://idp.unitelma.it/"
		}
		params = {
			"RelayState": relayState,
			"SAMLResponse": resp
		}
		r = session.post("https://elearning.unitelma.it/Shibboleth.sso/SAML2/POST", data=params, headers=heahder, allow_redirects=True)
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
		"User-Agent": USER_AGENT,
		"Referer": videoLink
	}
	r = session.get(videoLink, headers=headers)
	t = r.text
	id = t.split('src="https://elearning.unitelma.it/mod/kalvidres/lti_launch.php?')[1].split("entryid%2F")[1].split("%")[0]
	courseId = t.split("https://elearning.unitelma.it/course/view.php?id=")[1].split("\"")[0]
	if(VERBOSE):
		print(id)
	return id, courseId

def getKs(session, videoLink, mainId, courseId):
	if(VERBOSE):
		print("Obtaining kaf endpoint...", end=" ")
	headers = {
		"User-Agent": USER_AGENT,
		"Referer": videoLink
	}
	#TODO find a clean version of this link
	link = f'https://elearning.unitelma.it/mod/kalvidres/lti_launch.php?courseid={courseId}&height=602&width=658&withblocks=0&source=http%3A%2F%2Fkaltura-kaf-uri.com%2Fbrowseandembed%2Findex%2Fmedia%2Fentryid%2F{mainId}%2FshowDescription%2Ffalse%2FshowTitle%2Ftrue%2FshowTags%2Ffalse%2FshowDuration%2Ffalse%2FshowOwner%2Ftrue%2FshowUploadDate%2Ffalse%2FembedType%2FoldEmbed%2FplayerSize%2F602x658%2FplayerSkin%2F23448850%2FcrsId%2F1888%2FcmId%2F50969%2F'
	r = session.get(link, headers=headers)
	t = r.text
	endpoint = "https://" + t.split('<form action="https://')[1].split("/")[0]
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

	headers = {
		"User-Agent": USER_AGENT,
		"Referer": "https://elearning.unitelma.it/"
	}
	r = session.post(kafRefer, headers=headers, data=params)
	t = r.text
	lnk = t.split("window.location.href = '")[1].split("'")[0]
	if(VERBOSE):
		print("Done!")

	if(VERBOSE):
		print("Obtaining ks token...", end=" ")
	headers = {
		"User-Agent": USER_AGENT,
		"Referer": kafRefer
	}
	r = session.get(lnk, headers=headers)
	t = r.text
	ks = t.split('{"ks":"')[1].split('"')[0]
	if(VERBOSE):
		print(ks)
	return ks, endpoint

def getStreams(session, mainId, ksToken, kafEndpoint):
	if(VERBOSE):
		print("Asking for streams metadata...", end=" ")
	headers = {
		"User-Agent": USER_AGENT,
		"Referer": kafEndpoint + "/",
		"origin": kafEndpoint,
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
		"3:filter:entryIdEqual": "{1:result:objects:1:id}", #Official requests
		"4:ks": ksToken,
		"4:service": "flavorAsset",
		"4:action": "list",
		"4:filter:entryIdEqual": "{1:result:objects:0:parentEntryId}" #get the flavor of the mainId
	}
	r = session.post("https://kmc.l2l.cineca.it/api_v3/index.php?service=multirequest", headers=headers, data=params)
	j = r.json()
	allMetaData = j[0]["objects"]
	streamsData = j[1:]
	streams = []
	metaDataIdx = 0
	internalId = 0
	for stream in streamsData:
		qualityId = 0
		if("objects" not in stream):
			print(f"ERROR: Unable to fetch stream objects mdID={metaDataIdx}. Fullresponse: {j}")
			continue

		for highRes in stream["objects"]:
			tags = set()

			obj = {
				"internalId": internalId,
				"qualityId" : qualityId,
				"width": highRes["width"] if "width" in highRes else 0,
				"height": highRes["height"] if "height" in highRes else 0,
				"bitrate": highRes["bitrate"] if "bitrate" in highRes else 0,
				"framerate": highRes["frameRate"] if "frameRate" in highRes else 0,
				"entryId": highRes["entryId"] if "entryId" in highRes else "-",
				"flavorId": highRes["id"] if "id" in highRes else "-",
				"size": highRes["size"] if "size" in highRes else 0,

				"duration": 0,
				"description": "-",
				"searchText": "-",
				"name": "-",

				"durationStr": str(datetime.timedelta(seconds=0)),
				"bitrateStr": f"{convert_size(highRes['bitrate'])}ps",
				"sizeStr": convert_size(highRes["size"])
			}

			temp = highRes["tags"]
			temp = temp.split(",")
			for t in temp:
				tags.add(t.strip())
			
			if(metaDataIdx < len(allMetaData)):
				metaData = allMetaData[metaDataIdx]
				obj["duration"] = metaData["duration"] if "duration" in metaData else 0
				obj["name"] = metaData["name"] if "name" in metaData else "-"
				obj["description"] = metaData["description"] if "description" in metaData else "-"
				obj["searchText"] = metaData["searchText"] if "searchText" in metaData else "-"

				obj["durationStr"] = str(datetime.timedelta(seconds=metaData["duration"]))

				temp = metaData["tags"]
				temp = temp.split(",")
				for t in temp:
					tags.add(t.strip())

			obj["tags"] = tags
			obj["tagsStr"] = ", ".join(tags)

			streams.append(obj)
			internalId += 1
			qualityId += 1
		metaDataIdx += 1
	if(VERBOSE):
		print("Done!")
	return streams

def getDownloadLink(stream):
	return f"https://streaming.l2l.cineca.it/p/113/sp/11300/serveFlavor/entryId/{stream['entryId']}/v/2/flavorId/{stream['flavorId']}/forceproxy/true/name/a.mp4"


RESP_DOWNLOADED = 0
RESP_ALREADY_DWN = 1
RESP_UNABLE_TO_SELECT = 2
RESP_ERROR = 3
def downloadVideo(param):
	videoLink = None
	try: 
		videoLink = param["link"]
		print("\nDownloading: " + videoLink)
		mainId, courseId = getMainID(session, videoLink)
		ksToken, kafEndpoint = getKs(session, videoLink, mainId, courseId)
		streams = getStreams(session, mainId, ksToken, kafEndpoint)
		selectedStream = selectStream(streams, param)
		if(param["getInfo"] or selectedStream == None):
			s  = "\n"
			s += "".ljust(160, "-") + "\n"
			if(selectedStream == None):
				s += "    Unable to select the correct stream    "
			s += "    INFO for video: " + videoLink + "\n"
			s += "".ljust(160, "v") + "\n"
			print(s)
			for stream in streams:
				print()
				printStream(stream, videoLink)
				print()
			return RESP_UNABLE_TO_SELECT			
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
			if(not param["redownload"] and os.path.exists(fileName)):
				print(f"Skipping '{fileName}'; already download")
				return RESP_ALREADY_DWN
			else:
				download(downloadLink, fileName, kafEndpoint)
				print(fileName + "\t downloaded!")
				return RESP_DOWNLOADED
	except Exception as e:
		print("*** ERROR while downloading " + videoLink)
		print(e)
		return RESP_ERROR

def download(url, fileName, kafEndpoint):
	headers = {
		"authority": "streaming.l2l.cineca.it",
		"Referer": kafEndpoint,
		"User-Agent": USER_AGENT
	}
	response = requests.get(url, stream=True, headers=headers)
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
	resp = [[], [], [], []]
	i = 0
	for param in params:
		resp[downloadVideo(param)].append(i)
		i += 1
	print()
	if(len(resp[0]) > 0):
		print(f"Successfully downloaded: {resp[0]}")
	if(len(resp[1]) > 0):
		print(f"Already downloaded: {resp[1]}")
	if(len(resp[2]) > 0):
		print(f"Unable to select stream: {resp[2]}")
	if(len(resp[3]) > 0):
		print(f"Errors: {resp[3]}")
	if cmd is not None:
		if(VERBOSE):
			print("Executing " + cmd)
		os.system(cmd)
