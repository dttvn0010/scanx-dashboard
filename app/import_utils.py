import os
from django.shortcuts import HttpResponse
from django.core.files.storage import FileSystemStorage
import csv, json

fs = FileSystemStorage()

TMP_PATH = 'tmp'

def getPermutation(row, indexes):
    return [row[i] for i in indexes]

def importPreview(request, header):
    if request.method == 'POST':
        csvFile = request.FILES.get('csv_file')
        
        if csvFile and csvFile.name:
            tmpFilePath = os.path.join(TMP_PATH, csvFile.name)
            savedPath = fs.save(tmpFilePath, csvFile)

            with open(savedPath) as fi:
                reader = csv.reader(fi)
                csvHeader = next(reader)
                print(csvHeader)
                records = list(reader)
                request.session['records'] = records
                
            os.remove(savedPath)
            return HttpResponse(json.dumps({"header": header, "csvHeader": csvHeader}), 
                        content_type='application/json')

    else:
        return HttpResponse(json.dumps({"error": "Method not support"}), 
                    content_type='application/json')
