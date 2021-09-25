import Config, os, re, shutil

def concatStrings(arr): return '\n'.join([x for x in arr])

class Notify:
    def __init__(self):
        print(Config.GettedData['WelcomeText'])

    def do(self, text):
        if type(text) == list: text = ' '.join(str(x) for x in text)
        print(text)

    def wait(self):
        input('Type Enter...')

class SaveManager:
    def __init__(self, dataToSave):
        self.dataToSave = dataToSave

        try: os.mkdir('Results')
        except: pass

    def File(self, fileName):
        with open(os.path.join('Results', fileName + '.txt'), 'a+') as f: f.write('\n'.join(x for x in self.dataToSave))

    def Folder(self):
        for type in self.dataToSave:
            for path in self.dataToSave[type]:
                try: shutil.copytree(path, os.path.join(os.path.join('Results', type), os.path.basename(path)))
                except: pass

class Collector:
    def __init__(self, file):
        self.file = file

    def Discord(self):
        try:
            tokens = []
            with open(self.file, encoding = 'utf-8', errors = 'ignore') as f:
                f = f.read()
                for regex in [r'mfa\..{84}', r'.{24}\..{6}\..{27}']: tokens += re.findall(regex, f)
                return tokens
        except: return []

class Sort:
    def __init__(self, inputFolder):
        self.Statistic = {}

        self.inputFolder = inputFolder
        self.inputFiles = self.Walk(self.inputFolder)

        self.DiscordTokens = []
        self.CryptoWalletsFolder = {}
        self.BuildTags = {}
        self.Dates = {}

    def detectType(self, folder):
        for indicatorKey in Config.LogIndicators:
            if tuple(x in Config.LogIndicators[indicatorKey] for x in os.listdir(folder)).count(True) > Config.MinIndicatorMatches:
                if indicatorKey not in self.Statistic: self.Statistic[indicatorKey] = 0
                self.Statistic[indicatorKey] += 1
                return indicatorKey
        return False

    def grabDiscordTokens(self, folder, isTokens = True):
        for root, files, dirs in os.walk(folder):
            for path in files + dirs:
                if 'discord' not in path.lower() and isTokens: continue
                if os.path.isfile(os.path.join(root, path)): self.DiscordTokens += Collector(os.path.join(root, path)).Discord()
                else: self.grabDiscordTokens(os.path.join(root, path), False)

    def CryptoWallets(self, folder):
        for root, files, dirs in os.walk(folder):
            for path in files + dirs:
                for wallet in Config.CryptoWallets:
                    if wallet.lower() not in path.lower(): continue
                    if wallet not in self.CryptoWalletsFolder: self.CryptoWalletsFolder[wallet] = []
                    self.CryptoWalletsFolder[wallet].append(folder)

    def Walk(self, folder):
        validFolders = []
        if not folder or not os.path.exists(folder) or not os.path.isdir(folder): return []
        for nestedFolder in os.listdir(folder):
            if self.detectType(os.path.join(folder, nestedFolder)): validFolders.append(os.path.join(folder, nestedFolder))
            else: validFolders += self.Walk(os.path.join(folder, nestedFolder))
        return validFolders

    def byDate(self, folder):
        if self.detectType(folder) == 'RedLine':
            if not os.path.exists(os.path.join(folder, 'UserInformation.txt')): return
            with open(os.path.join(folder, 'UserInformation.txt'), errors = 'ignore') as f:
                f.seek(850)
                DateFile = re.search('\d+/\d+/\d+', f.read(250))[0].replace('/', '.')
            if DateFile not in self.Dates: self.Dates[DateFile] = []
            self.Dates[DateFile].append(folder)
            return

    def byBuildTag(self, folder):
        if self.detectType(folder) == 'RedLine':
            if not os.path.exists(os.path.join(folder, 'UserInformation.txt')): return
            with open(os.path.join(folder, 'UserInformation.txt'), errors = 'ignore') as f:
                f.seek(350)
                BuildId = re.search('Build ID: .+', f.read(200))[0].split(': ')[-1]
            if BuildId not in self.BuildTags: self.BuildTags[BuildId] = []
            self.BuildTags[BuildId].append(folder)
            return

if __name__ == '__main__':
    notify = Notify()
    Sorted = Sort(input('Type path to folder with your files: '))

    for log in Sorted.inputFiles:
        Sorted.grabDiscordTokens(log)
        Sorted.CryptoWallets(log)
        Sorted.byBuildTag(log)
        Sorted.byDate(log)


    SaveManager(Sorted.Dates).Folder()
    SaveManager(Sorted.BuildTags).Folder()
    SaveManager(Sorted.CryptoWalletsFolder).Folder()
    SaveManager(Sorted.DiscordTokens).File('Discord')

    notify.do('Log Types: ')
    for logType in Config.LogIndicators: notify.do(['\t', logType, ':', Sorted.Statistic[logType]])

    notify.do('Log Dates: ')
    for date in Sorted.Dates: notify.do(['\t', date])

    notify.do(['Discord Tokens:', len(Sorted.DiscordTokens)])

    notify.do('Build Tags: ')
    for tag in Sorted.BuildTags: notify.do(['\t', tag])

    notify.wait()
