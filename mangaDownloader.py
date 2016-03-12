import os
import urllib
import urllib.request
from bs4 import BeautifulSoup

def doesFolderExist(folderName):
	if os.path.exists(folderName):
		return True
	else:
		return False

def createFolder(folderName):
	if not os.path.exists(folderName):
		os.makedirs(folderName)

def saveImage(stream, folderName, imageName):
	createFolder(folderName)
	fileName = folderName + '/' + imageName + '.jpg'
	file = open(fileName,'wb')
	file.write(stream)
	file.close()

def getHTMLStream(url):
	hdr = {'User-Agent': 'Mozilla/5.0'}
	request = urllib.request.Request(url, headers = hdr)
	rawHTML = urllib.request.urlopen(request)
	return rawHTML

def downloadManga():
	baseURL = 'http://mangareader.net'
	mangaName = ''	#space separated name of manga as on mangareader.net
	mangaNameWithDelimiter = mangaName.replace(' ', '-')

	rawHTML = getHTMLStream(baseURL + '/' + mangaNameWithDelimiter)
	soup = BeautifulSoup(rawHTML, 'html.parser')
	chapters = soup.find('div', {'id' : 'chapterlist'}).find_all('div', {'class' : 'chico_manga'})
	chapterIndex = 0

	for i in chapters:
		chapterIndex = chapterIndex + 1
		if doesFolderExist(str(chapterIndex)) == True:
			continue
		chapterURL = i.parent.find_all('a')[0]['href']
		runningChapterURL  = baseURL + chapterURL;
		print(runningChapterURL)		
		rawHTML = getHTMLStream(runningChapterURL)
		soup = BeautifulSoup(rawHTML, 'html.parser')

		options = soup.find( 'select' , {'id' : 'pageMenu'}).find_all('option')
		imageNumber = 0
		for j in options:
			imageNumber = imageNumber + 1
			currentPageURL = baseURL + j['value']
			lRawHTML = getHTMLStream(currentPageURL)
			lSoup = BeautifulSoup( lRawHTML, 'html.parser' )
			imageLink = lSoup.find( 'div', {'id' : 'imgholder'} ).find_all( 'a' )[0].find_all( 'img' )[0][ 'src' ]
			lRawHTML = getHTMLStream(imageLink)
			stream = lRawHTML.read()
			saveImage(stream, str(chapterIndex), str(imageNumber))
			
if __name__ == '__main__':
    downloadManga()