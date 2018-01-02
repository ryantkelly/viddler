# About

This is class for downloading published source videos from Viddler using the available API.

# Requirements
`requests` and `furl`

# Usage

Required class arguments are:

- **api_key**: Your Viddler API key
- **user**: Viddler username
- **password**: Viddler password
- **save_dir**: Directory to save downloaded videos to

An example of downloading all published, source videos for an account:
```
from viddler import Viddler

v = Viddler(api_key, user, password, save_dir)

for video in v.videos:
    if video['id'] not in v.loadProgress()['complete']: # If complete, do not download
        result = v.downloadVideo(video)
        if result == True:
            print(video['title'] + ' downloaded!') # Video was status of 'ready', so downloaded
        else:
            print(video['title'] + ' not published, ignored.') # Video was NOT status of 'ready', so ignored

v.makeWebpage() # Create a webpage of the downloaded videos
```

If you want to download all videos (published/unpublished), or versions other than source, modify the `downloadVideo()` method.

# Support files

## auth.json
Caches Viddler authentication. If `requests` raises a failure status, the class reauthenticates. If you are constantly getting HTTP errors, delete this file.

## videos.json
File containing a json array of all videos for the defined Viddler account, saved to .json for caching purposes.

If this file doesn't exist, it is created upon instantiation of the class. If it does exist, it will just be read into the new instance. So, you can delete this if you need to start over or need the freshest data.

## progress.json
File containing statuses (complete, fail, etc) and the video ids that had that status. Currently, only a status of `complete` is written after download is complete.

Useful to prevent downloading already completed videos or validating that downloads have been completed.

## video_info.csv
This file contains video meta data, and is saved in the `save_dir`.

Example:

| Video ID | Thumb | Location | Title | Description | Published | View Count | Impression Count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 66a80731 | thumbs/bike race.jpg | save_dir/videos/bike race.mov	| A bicycle race | This was a great bicycle race, everyone had fun. | 12/8/16 12:25 | 10000 | 10000 |

# Other helpful methods

## makeWebpage()
Reads the `video_info.csv` file and make a Bootstrap-styled web page, for easier browsing. Will also display video thumbnails.

## makePublic() and makePrivate()
Before videos are downloaded, they are made public. Upon completion of the download, they are made private. Additionally, these methods are useful if you need to make a bunch of videos only privately downloaded.