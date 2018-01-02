import requests, json, os, csv, datetime, re, codecs
from furl import furl
import sys
class Viddler():
    viddler = "https://api.viddler.com/api/v2/"
    
    video_file = 'videos.json'
    auth_file = 'auth.json'
    meta_file = 'video_info.csv'
    progress_file = 'progress.json'
    regex = re.compile('[/.*\':?|#]')

    def __init__(self, api_key, user, password, save_dir):
        self.api_key = api_key
        self.save_dir = save_dir
        self.user = user
        self.password = password

        if not os.path.isdir(self.save_dir): # create save dir
            os.makedirs(self.save_dir)

        self.video_dir = os.path.join(self.save_dir, 'videos')
        if not os.path.isdir(self.video_dir): # create video dir
            os.makedirs(self.video_dir)

        self.thumb_dir = os.path.join(self.save_dir, 'thumbs') # create thumbs dir
        if not os.path.isdir(self.thumb_dir):
            os.makedirs(self.thumb_dir)

        if os.path.isfile(self.auth_file): #create or read auth file
            self.auth = json.load(open(self.auth_file))
        else:
            try:
                self.authenticate()
            except:
                raise

        if os.path.isfile(self.video_file): #create or read videos file
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
                try:
                    d[status].append(_id)
                except KeyError:
                    d[status] = [_id]
            with open(self.progress_file, 'w') as f:
                f.write(json.dumps(d))

        except FileNotFoundError:
            with open(self.progress_file, 'w') as f:
                d = {}
                d[status] = [_id]
                f.write(json.dumps(d))
    
    def loadProgress(self):
        """Loads progress file"""
        try:
            d = json.load(open(self.progress_file, 'r'))
        except:
            raise
        return(d)

    def downloadVideo(self, video):
        """Download a video from a json object"""
        for _file in video['files']:
            if _file['profile_name'] == "Source":
                if _file['status']=='ready':
                    self.makePublic(video['id'])
                    dest = os.path.join(self.video_dir, self.regex.sub('', video['title'])+'.'+_file['ext'])
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
                    self.downloadThumb(video)
                    self.makePrivate(video['id'])
                    self.saveVideoMeta(video)
                    self.writeProgress(video['id'], 'complete')
                    return True
                else:
                    return False
    
    def downloadThumb(self, video):
        """Download thumbnail image for the video"""
        dest = os.path.join(self.thumb_dir, self.regex.sub('', video['title'])+'.jpg')
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
                writer.writerow(['Video ID', 'Thumb', 'Location', 'Title', 'Description', 'Published', 'View Count','Impression Count'])
        
        for _file in video['files']:
            if _file['profile_name'] == "Source":
                break
        pub = datetime.datetime.fromtimestamp(int(video['made_public_time'])).strftime('%Y-%m-%d %H:%M:%S')
        with open(dest, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(
                [video['id'],
                os.path.join('thumbs', self.regex.sub('', video['title'])+'.jpg'), 
                os.path.join(self.video_dir, self.regex.sub('', video['title'])+'.'+_file['ext']),
                video['title'], 
                video['description'], 
                pub, 
                video['view_count'], 
                video['impression_count']])

    def makeWebpage(self, file_name):
        """Make a web page to browse downloaded videos"""
        
        # Download Bootstrap CSS for table
        try:
            result = requests.get("https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.3/css/bootstrap.min.css") 
            # Yes, this is hard coded. I should probably grab from GitHub. And I'm also sure there's a better way to do this.
        except:
            raise
        with open(os.path.join(self.save_dir, 'bootstrap.min.css'), 'w') as f:
            f.write(result.text) 
        f = open(os.path.join(self.save_dir, file_name), 'w')
        f.write("""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>Viddler Archive</title>
                <link href="bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
            <table class="table table-striped table-hover">""")

        with codecs.open(os.path.join(self.save_dir, self.meta_file), "r",encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.reader(csvfile, dialect="excel")
            count = 0
            for row in reader:
                if count == 0:
                    f.write('<thead class="thead-default"><tr>')
                    for c in row:
                        f.write("<th>"+c+"</th>")
                    f.write("</thead></tr>")
                else:
                    f.write("<tr>")
                    for i, c in enumerate(row):
                        if i==1: #Thumb image
                            s = '<img class="img-thumbnail" src="'+c+'"/>'
                        else:
                            s = c
                        f.write("<td>"+s+"</td>")
                    f.write("</tr>")
                count+=1
        f.write("</table></body></html>")