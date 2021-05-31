# You can use whatever package(s) you like to handle the timeseries data
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ast
from datetime import datetime, timedelta 


class VISCalculator:

    def __init__(self, medications_filename, medication_administrations_filename, note_filename, procedures_filename):
        self.medications_filename=medications_filename
        self.medication_administrations_filename =  medication_administrations_filename
        self.note_filename=note_filename
        self.procedures_filename=procedures_filename
#To get the FHIR Procedure_resource
    def make_procedures_from_log(self):
        df = pd.read_csv("../../data/"+self.procedures_filename)
        d={'procedure':[]}
        for i in range(len(df)):
            x={}
            x['procedure_subject']=(df.loc[i,'mrn'])
            x['procedure_code']=(df.loc[i,'case_id'])
            x['procedure_performed']=(df.loc[i,'primary_surgeon'])
            x['procedure_date']=[{'procedure_date': df.loc[i,'procedure_date']},
                              {'procedure_time': (df.loc[i,'procedure_time'])} ]
            d['procedure'].append(x)
        return d
# To extract data from Parsed note
    def make_procedures_from_note(self):
        with open(self.note_filename,"r+") as f:
            s=f.read()
            d=ast.literal_eval(s)
        l=[]
        for i in d['coded_entities']:
            if i.get('value') is not None:
                l.append([i['text'],i['value']])

            else:
                l.append(i['text'])
        return l

#To get Patient resource

    def resource_patient(self):
        l=VISCalculator.make_procedures_from_note(self)
        d={'Name':[],'Date':[],'Sex':[],'Birth Date':[],'Hospital Admission':[],'Hospital Discharge':[],'ICU admission date':[],
      'ICU discharge date': [],'Atrial Septal Defect':[],'Echocardiogram':[]}
        a=1000
        for i in range(len(l)):
            if type(l[i])!= list and l[i].lower()=='name'   :
                d['Name'].append(l[i+1][1])
            if type(l[i])!= list and l[i].lower()=='date':
                d['Date'].append(l[i+1][1])
            if type(l[i])!= list and  (l[i].lower()=="male" or l[i].lower()=='female'):
                d['Sex'].append(l[i])
            if type(l[i])!= list and l[i].lower()=='birth date':
                d['Birth Date'].append(l[i+1][1])

            if type(l[i])!= list and l[i].lower()=='encounter' :
                a=i
            if  i>a :

                if  'hospital admission' in l[i][0].lower() : 
                    d['Hospital Admission'].append(l[i][1])
                if  'hospital discharge' in l[i][0].lower() : 
                    d['Hospital Discharge'].append(l[i][1])
                if 'icu admission' in l[i][0].lower() : 
                    d['ICU admission date'].append(l[i][1])
                if  'icu discharge' in l[i][0].lower() : 
                    d['ICU discharge date'].append(l[i][1])
                if type(l[i])!= list and l[i].lower()=='atrial septal defect':
                    if type(l[i])!= list and (l[i+1].lower() =='diagnosed'):
                        d['Atrial Septal Defect'] =True
                    else:
                        d['Atrial Septal Defect'] =False
                if  'echocardiogram'in l[i][0].lower():
                    d['Echocardiogram'].append(l[i][1])
        return d

    def make_encounters_from_note(self):
        pass

    def make_fhir_resources(self):
        pass
#To read medication_adminstrations_note

    def read_medication_administrations_filename(self):
        with open("../../data/"+self.medication_administrations_filename,"r+") as f:
            d=json.load(f)   
        return d
    def calculate_vis_timeseries(self):
        d=VISCalculator.resource_patient(self)
        hospital_admission=  '2/2/2000 2pm'
        hospital_discharge=  '2/5/2000 12pm'

        h_adm=datetime.strptime(hospital_admission, "%m/%d/%Y %I%p")
        h_dis=datetime.strptime(hospital_discharge, "%m/%d/%Y %I%p")
        x=read_medication_administrations_filename(medication_administrations_filename)
        l=[]
        for i in x:
            l.append([i["rateQuantity"]["value"],i["effectivePeriod"]["start"],i["effectivePeriod"]["end"]])
        ds=[]
        for i in l:
            d=datetime.strptime(i[1], "%Y-%m-%dT%H:%M:%S")
            d1=datetime.strptime(i[2], "%Y-%m-%dT%H:%M:%S")
            if (d>h_adm) and (d<h_dis):
            
                ds.append([i[0],d,d1])
    
        return ds
    def vis_raw_file(ds):
        with open("../results/"+"VIS_timeseries.csv",'w') as f:    
            s="VIS_Scores,TimeStamp\n"
            for i in ds:
                s+=str(i[0])+","+i[1].strftime("%Y-%m-%dT%H:%M:%S")+","+i[1].strftime("%Y-%m-%dT%H:%M:%S")+"\n"
                f.write(s)
                s=""

#There was an issue with Hospital Discharge date i.e. that Hospital Discharge date = Hospital Admission Date
#I also re-verified manually with parsed_data_set.
#therefore I took Hospital Discharge date and Hospital Admission Date from raw-sample-note    
#The problem was also repeated for ICU Admission time and ICU Discharge time 
#The time mentioned in parsed note does not match Raw_note
    def plot_vis_timeseries(self):
        ds=VISCalculator.calculate_vis_timeseries(self)
        hospital_admission=  '2/2/2000 2pm'
        hospital_discharge=  '2/5/2000 12pm'
        h_adm=datetime.strptime(hospital_admission, "%m/%d/%Y %I%p")
        h_dis=datetime.strptime(hospital_discharge, "%m/%d/%Y %I%p")
        ds.insert(0,[0,h_adm])
        ds.append([0,h_dis])
        x = np.array([i[1].strftime("%d %H") for i in ds])
        y = np.array([i[0] for i in ds])
        plt.xlabel("X axis Admission_Date(Day,Hour)")
        plt.ylabel("Y axis Vis_Score")
        plt.plot(x,y)
        plt.show()
        plt.savefig("../results/"+'VIS_timeseries.png')


#The problem was also repeated for ICU Admission time and ICU Discharge time 
#The time mentioned in parsed note does not match Raw_note

    def get_max_vis_score_info(self):
        ds=VISCalculator.calculate_vis_timeseries(self)
        d=VISCalculator.resource_patient(self)
        cicu_adm=datetime.strptime(d['ICU admission date'][0], "%Y-%m-%dT%H:%M:%S")
        cicu_dis=datetime.strptime(d['ICU discharge date'][0], "%Y-%m-%dT%H:%M:%S")
        m_vis,m1_vis =0,0
        m_vis_timestamp=""
        for i in ds:
            #print(i)
            if (i[1] >cicu_adm) and (i[1]<cicu_adm + timedelta(days=1)):
                m_vis=max(m_vis,i[0])
                if m_vis==i[0]:
                    m_vis_timestamp=i[1]
                    effect_time=i[2]-i[1]
                    print(i[1],i[2],effect_time)
                    duration=effect_time.total_seconds()/60
            if (i[1] >cicu_adm + timedelta(days=1)) and (i[1]<cicu_adm + timedelta(days=2)):
                m1_vis=max(m1_vis,i[0])
        p_category=''
        if m_vis <10 and m1_vis <5:
            p_category='Group_1'
        elif m_vis <15 and m1_vis <10:
            p_category='Group_2'
        elif m_vis <20 and m1_vis <15:
            p_category='Group_3'
        elif m_vis <25 and m1_vis <20:
            p_category='Group_4'
        else:
            p_category='Group_5'
        return m_vis,m_vis_timestamp,duration,p_category
