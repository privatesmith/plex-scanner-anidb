#
# AniDB is a scanner that will parse files renamed using KADR using something
# approximating the following format:
# %anime_name_romaji% - %episode% - %episode_name% - [%group_short%](%crc32%).%filetype%
#

import re, os, os.path
import sys
import Media, VideoFiles, Stack, Utils

# parse episode number
def parseEpisode(ep, season=1, offset=0):
  print("ep: {}, season: {}, offset: {}".format(ep, season, offset))
  ep = ep.split('v')[0]
  try:
    int(ep)
    return [[season, int(ep) + offset]]
  except ValueError:
    if season > 0:
      if ep[0:1].upper() == 'S':
        return parseEpisode(ep[1:], 0)
      elif ep[0:1].upper() == 'C':
        return parseEpisode(ep[1:], 0, 100)
      elif ep[0:1].upper() == 'T':
        return parseEpisode(ep[1:], 0, 200)
      elif ep[0:1].upper() == 'P':
        return parseEpisode(ep[1:], 0, 300)
      elif ep[0:1].upper() == 'O':
        return parseEpisode(ep[1:], 0, 400)
      else:
        if ep.find('-') > 0:
          mep = ep.split('-')
          mepr = []
          try:
            for ep in range(int(mep[0]), (int(mep[1]) + 1)):
              mepr.append([season, int(ep) + offset])
          except:
            pass
          finally:
            if len(mepr) > 0:
              return mepr
            else:
              return None
    else:
      return None

def findGroup(title):
    return re.split('[\[\]]', title)[1]

def cleanTitle(title):
    title = title.replace(';', ' ')
    title = title.replace(':', '')
    return title

# Scans through files, and add to the media list.
def Scan(path, files, mediaList, subdirs, language=None, root=None):
  # Just look for video files.
  VideoFiles.Scan(path, files, mediaList, subdirs, root)

  # Add them all.
  for path in files:
    (show, year) = VideoFiles.CleanName(os.path.basename(path))
    file = Utils.SplitPath(path)[-1]
    ext = file.split('.')[-1]
    name = '.'.join(file.split('.')[0:-1])
    nameChunks = name.split(' - ')

    for i, chunk in enumerate(nameChunks):
        if parseEpisode(chunk):
            nameChunks = [' - '.join(nameChunks[:i]), nameChunks[i], ' - '.join(nameChunks[i+1:])]
            break

    # correct for "-" in show name or title
    if len(nameChunks) > 4:
      if parseEpisode(nameChunks[1]) == None:
        if len(nameChunks[1]) >= 4:
          if parseEpisode(nameChunks[2]) <> None:
            extra = nameChunks.pop(1)
            nameChunks[0] = "%s - %s" % (nameChunks[0], extra)
      else:
        while len(nameChunks) > 4:
          extra = nameChunks.pop(3)
          nameChunks[2] = "%s - %s" % (nameChunks[2], extra)

    try:
      sep = parseEpisode(nameChunks[1])
      if sep <> None:
        if len(sep) == 1:
          anime_ep = Media.Episode(cleanTitle(nameChunks[0]), sep[0][0], sep[0][1], nameChunks[2])
          anime_ep.source = findGroup(nameChunks[2])
          anime_ep.parts.append(path)
          mediaList.append(anime_ep)
        else:
          for ep in sep:
            beginEp = sep[0][1]
            endEp = sep[-1][1]

            anime_ep = Media.Episode(cleanTitle(nameChunks[0]), ep[0], ep[1], nameChunks[2])
            anime_ep.source = findGroup(nameChunks[2])
            anime_ep.display_offset = (ep[1]-beginEp)*100/(endEp-beginEp+1)
            anime_ep.parts.append(path)
            mediaList.append(anime_ep)
    except:
      with open('/tmp/adb-unmatchables.log', 'a') as log:
        log.write("%s\n" % file)

if __name__ == '__main__':
  path = sys.argv[1]
  files = [os.path.join(path, file) for file in os.listdir(path)]
  media = []
  Scan(path[1:], files, media, [])
  print "Media:", media
