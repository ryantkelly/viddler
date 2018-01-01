import requests, json, os, pprint, csv, datetime
from furl import furl
import sys
class Viddler():
    viddler = "https://api.viddler.com/api/v2/"
    
    video_file = 'videos.json'
    auth_file = 'auth.json'
    meta_file = 'video_info.csv'
    progress_file = 'progress.json'

    def __init__(self, api_key, user, password, save_dir):
        self.api_key = api_key
        self.save_dir = save_dir
        self.user = user
        self.password = password
        if not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir)

        if os.path.isfile(self.auth_file):
            self.auth = json.load(open(self.auth_file))
        else:
            self.authenticate()

        if os.path.isfile(self.video_file):
            self.videos = json.load(open(self.video_file))
        else:
            self.videos = self.getVideos()

    def authenticate(self):
        """Authenticates and saves token to auth.json file"""
        params = {
            'user': self.user,
            'password': self.password,
            'get_record_token': 1,
            'api_key': self.api_key
        }
        url = furl(self.viddler+'viddler.users.auth.json').add(params)
        try:
            auth = requests.get(url)
        except:
            raise
        self.auth = auth.json()
        self.saveJson(self.auth_file, auth.json())
        
        
    def saveJson(self, _file, _dict):
        """Function to write dict to json"""
        with open(_file, 'w') as f:
            f.write(json.dumps(_dict))

    def getVideos(self):
        """Gets all videos for account, and write to videos.json for caching purposes"""
        f = open(self.video_file, 'w')
        _list = []
        params = {
            'sessionid': self.auth['auth']['sessionid'],
            'api_key': self.api_key,
            'user': self.user,
            'per_page': 100
        }
        params2 = params

        page = 0
        data = True
        while data == True:
            page = page + 1
            params2['page'] = page
            url = furl(self.viddler+'viddler.videos.getByUser.json').add(params2)
            try:
                result = requests.get(url)
            except:
                raise
            result.raise_for_status()
            if result.json()['list_result']['video_list']:
                for video in result.json()['list_result']['video_list']:
                    _list.append(video)
            else:
                data = False
        f.write(json.dumps(_list))
        return json.load(open(self.video_file))

    def makePublic(self, _id):
        """Make a video publically downloadable"""
        params = {
            'sessionid': self.auth['auth']['sessionid'],
            'api_key': self.api_key,
            'video_id': _id,
            'download_perm': 'public'
        }
        url = furl(self.viddler+'viddler.videos.setDetails.json').add(params)
        try:
            result = requests.post(url)
        except:
            raise
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError:
            self.authenticate()

    def makePrivate(self, _id):
        """Make video not publically downloadable"""
        params = {
            'sessionid': self.auth['auth']['sessionid'],
            'api_key': self.api_key,
            'video_id': _id,
            'download_perm': 'private'
        }
        url = furl(self.viddler+'viddler.videos.setDetails.json').add(params)
        try:
            result = requests.post(url)
        except:
            raise
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError:
            self.authenticate()

    def writeProgress(self, _id, status):
        """Write the progress (complete, failed, other) to json"""
        try:
            with open(self.progress_file, 'r+') as f:
                d = json.loads(f.read())
                d.append({_id: status})
            with open(self.progress_file, 'w') as f:
                f.write(json.dumps(d))
        except FileNotFoundError:
            with open(self.progress_file, 'w') as f:
                d = [{_id: status}]
                f.write(json.dumps(d))
    
    def loadComplete(self):
        """Loads complete files into a list"""
        try:
            d = json.load(open(self.progress_file, 'r'))
        except:
            raise
        l = []
        for p in d:
            if list(p.values())[0]  == 'complete':
                l.append(list(p.keys())[0])
        return l

    def downloadVideo(self, video):
        """Download a video from a json object"""
        for _file in video['files']:
            if _file['profile_name'] == "Source":
                if _file['status']=='ready':
				    self.makePublic(video['id'])
					dest = os.path.join(self.save_dir, video['id']+'.'+_file['ext'])
					try:
						result = requests.get(_file['url'], stream=True)
					except:
						raise
					try:
						result.raise_for_status()
					except requests.exceptions.HTTPError:
						self.authenticate()

					with open(dest, 'wb') as f:
						for chunk in result.iter_content(chunk_size=1024):
							if chunk:
								f.write(chunk)
					self.makePrivate(video['id'])
					self.saveVideoMeta(video)
					self.writeProgress(video['id'], 'complete')
					return True
				else:
					return False
    
    def downloadThumb(self, video):
        """Download thumbnail image for the video"""
        thumb_dir = os.path.join(self.save_dir, 'thumbs')
        if not os.path.isdir(thumb_dir):
            os.makedirs(thumb_dir)
        
        dest = os.path.join(thumb_dir, video['id']+'.jpg')
        try:
            result = requests.get(video["thumbnail_url"])
        except:
            raise
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError:
            self.authenticate()
        with open(dest, 'wb') as f:
            f.write(result.content)

    def saveVideoMeta(self, video):
        """Write some video meta data to a .csv"""
        dest = os.path.join(self.save_dir, self.meta_file)
        if not os.path.isfile(dest):
            with open(dest, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['Video ID', 'Directory', 'Filename', 'Title', 'Description', 'Published', 'View Count','Impression Count'])
        
        for _file in video['files']:
            if _file['profile_name'] == "Source":
                break
        pub = datetime.datetime.fromtimestamp(int(video['made_public_time'])).strftime('%Y-%m-%d %H:%M:%S')
        with open(dest, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([video['id'], self.save_dir, video['id']+'.'+_file['ext'], video['title'], video['description'], pub, video['view_count'], video['impression_count']])

    def makeWebpage(self):
        """Make a web page to browse downloaded videos"""