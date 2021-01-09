from useful import *
def gitChangedRecently(component, files):
	from os import chdir, getcwd
	from os.path import join
	currentDir = getcwd()
	chdir(getcwd() + "/" +component)
	lines = execute('git status -s')
	for line in lines[1:]:
		if line[:3] == " M ":
			filename = line.rstrip()[3:]
			if ".DS_Store" not in filename:
				files.append(join(component,filename))
	
	lines = execute('git ls-files -o  --exclude-standard')
	for line in lines[1:]:
		filename = line.rstrip()
		if ".DS_Store" not in filename:
			files.append(join(component,filename))
	
	chdir(currentDir)

def zipFiles(zipFilename, directory, files, display=True):
	from zipfile import ZipFile, ZIP_DEFLATED 
	from os.path import join, normpath
	
	files.sort()
	if len(files) > 0:
		archive = ZipFile(zipFilename,"w", ZIP_DEFLATED)
		if display:
			print("Zip %s"%zipFilename)
		for file in files:
			try:
				archive.write(normpath(join(directory, file)), file)
				if display:
					print("+ %s"%(file))
			except:
				if display:
					print("- %s"%(file))
				pass
	else:
		print("Zip %s empty"%zipFilename)

if __name__ == "__main__":
	files = []
	gitChangedRecently("firmware/micropython",files)
	gitChangedRecently("firmware/esp-idf",files)
	gitChangedRecently("firmware/esp-idf/components/esp32-camera",files)
	from time import localtime, time, strftime
	filename = strftime("firmware/BackupGit__%Y.%m.%d__%H-%M-%S.zip",localtime(time()))

	zipFiles(filename,".",files,True)