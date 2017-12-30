# About

This is class for downloading source videos from Viddler. Feel free to take what is in here and use in your own projects!

# Requirements
`requests` and `furl`

# Usage

Required class arguments are:

- **api_key**: Your Viddler API key
- **user**: Viddler username
- **password**: Viddler password
- **save_dir**: Directory to save downloaded videos to

An example of downloading all videos for an account:
```
from viddler import Viddler

v = Viddler(api_key, user, password, save_dir)

for video in v.videos:
    v.downloadVideo(video)
```

# Support files

## auth.json
Caches Viddler authentication. If `requests` raises a failure status, the class reauthenticates. If you are getting HTTP errors, delete the auth.json file.

## videos.json
File containing a json array of all videos for the defined Viddler account, saved to .json for caching purposes.

If this file doesn't exist, it is created upon instantiation of the class. If it does exist, it will just be read into the new instance. So, you can delete this if you need to start over/have the freshest data.

## progress.json
File containing video ids and their status. Currently, only a status of `complete` is written after download is complete.

Useful to prevent downloading already completed videos.

## video_info.csv
This file contains video meta data, and is saved in the `save_dir`.