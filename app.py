import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import re
from re import finditer
import plotly.graph_objs as go

url = "https://data.ojp.usdoj.gov/api/views/6h3w-ci9p/rows.csv?accessType=DOWNLOAD&amp;bom=true&amp;format=true"
program = pd.read_csv(url, encoding='utf-8-sig')
num_of_programs = len(program)
# list(program['Randomized Controlled Trial']).count('Randomized Controlled Trial'), len(program)

# # topics
# topic = list(set(program['Topics']))
# topic = ", ".join(topic)
# topic = topic.split(", ")
# topic = list(set(topic))
# topic.sort()

# categories
test = program['Program Type'].to_list()
test = [x for x in test if type(x)==str]
test = ', '.join(test)
test = test.split(", ")
category = list(set(test))

# classify with some criteria
treat = [x for x in category if 'group home' in x.lower() or
        'camp' in x.lower() or 'aftercare' in x.lower() or 
        'shelter' in x.lower() or 'school' in x.lower() or
        'classroom' in x.lower() or 'residential' in x.lower()]
cognitive = [x for x in category if 'vocational' in x.lower() or 
            'restorative' in x.lower() or 'academic' in x.lower() or
            'motivational' in x.lower() or 'mentoring' in x.lower()]
therapy = [x for x in category if 'drug' in x.lower() or 
          'therapeutic' in x.lower() or 'mental health' in x.lower() or 
          'weed' in x.lower() or 'therapy' in x.lower()]
deter = [x for x in category if 'crime' in x.lower() or
        'violence' in x.lower() or 'bullying' in x.lower() or
        'deter' in x.lower() or 'policing' in x.lower()]

# define function to get the treatment status
def getTreat(STRING, Category, Cat_str):
    Container = str(STRING).split(", ")
    output = 0
    for element in Category:
        if element in Container:
            output=1
    return output

# topic columns
for E in ['reentry', 'court', 'crime', 'drug', 'juvenile', 'le', 'tf', 'victim']:
    col = "topic_" + E
    program[col] = program['Topics'].apply(lambda x: 1 if E in str(x).lower() else 0)

# dummies for each classification
program['rct'] = program['Randomized Controlled Trial'].apply(lambda x: 1 if x=='Randomized Controlled Trial' else 0)
program['treat'] = program['Program Type'].apply(lambda x: getTreat(x, treat, 'treat'))
program['therapy'] = program['Program Type'].apply(lambda x: getTreat(x, therapy,'therapy'))
program['cognitive'] = program['Program Type'].apply(lambda x: getTreat(x, cognitive, 'cognitive'))
program['deter'] = program['Program Type'].apply(lambda x: getTreat(x,deter,'deter'))
program['other'] = program.apply(lambda x: 1 if x['treat']!=1 and 
                                 x['therapy'] != 1 and x['cognitive'] != 1 and x['deter'] != 1
                                 else 0, axis=1)
# years of publication
title = ['InterventionPublic_ID','Evidence Rating', 'Program Type',
         'Randomized Controlled Trial','Program Description',
         'Geography', 'Gender',
         'topic_reentry', 'topic_court', 'topic_crime', 'topic_drug',
       'topic_juvenile', 'topic_le', 'topic_tf', 'topic_victim', 'rct',
       'treat', 'therapy', 'cognitive', 'deter', 'other']
pub = []
for i in range(len(program)):
    text = program['Evaluation Methodology'].values[i]
    sep = []
    # should get rid of study \d keywords other than the actual one
    for j in range(1,4):
        if re.findall('Study '+str(j), text) != [] and text.count('Study '+str(j)) > 1:
            text = 'Study '+str(j) + "".join(text.split('Study '+str(j)))
    for match in finditer('Study \d',text):
        sep.append(match.span()[1])
    sep.sort()
    sep.append(len(text))
    studies = []
    for j in range(1,len(sep)):
            studies.append(text[sep[j-1]:sep[j]])
    for j in range(len(studies)):
        yr = 'na'
        if re.findall('\d{4}', studies[j]) != []:
            yr = re.findall('\d{4}', studies[j])[0]
        pub.append(list(program[title].values[i]) + [yr, studies[j]])
data = pd.DataFrame(pub, columns = title+['pub_yr','method'])

data['number'] = list(range(len(data)))
data = data[data['pub_yr']!='na']
data['pub_yr_cat'] = data['pub_yr'].apply(lambda x: str(x)[:3]+"0")
data = data[~data['Program Type'].str.contains('Victim',na=False, regex=True)] # ignore programs with victim for now

# rating
data['rating'] = list(data['Evidence Rating'])
data['rating'] = data['rating'].apply(lambda x: "Effective" if x=='Effective - More than one study' else x)
data['rating'] = data['rating'].apply(lambda x: "Effective" if x=='Effective - One study' else x)
data['rating'] = data['rating'].apply(lambda x: "Promising" if x=='Promising - More than one study' else x)
data['rating'] = data['rating'].apply(lambda x: "Promising" if x=='Promising - One study' else x)
data['rating'] = data['rating'].apply(lambda x: "No Effects" if x=='No Effects - One study' else x)
data['rating'] = data['rating'].apply(lambda x: "No Effects" if x=='No Effects - More than one study' else x)

# set colors
df = data.groupby(['treat','pub_yr_cat'],as_index=False).agg('count')
bar = list(set(df['pub_yr_cat']))
bar.sort()
colors = {'treat':'royalblue', 'therapy':'crimson', 'cognitive':"lightseagreen",
         'deter':'orange', 'other':'lightgrey'}

lis_treat = []
for i in ['treat','therapy','cognitive','deter','other']:
    test = data.groupby([i,'pub_yr_cat'],as_index=False).agg('count')
    lis_treat.append(go.Bar(name=i[0].upper() + i[1:], x=bar, 
                            y=list(test['rating'][test[i]==1]),
                            marker={'color': colors[i]}))
figure={'data': lis_treat,
            'layout':
            go.Layout(title='Agenda each decade (Not mutually exclusive)', barmode='group')}

dd = [
       ['Treat','Practices Focused on Group Activities - target of analysis'],
       ['Therapy', "Therapeutic Practices"],
       ['Cognitive','Cognitive Training'],
       ['Deter','Practices Focused on Deterrence'],
       ['Other',"Other Practices Than Aforementioned Categories"]
      ]
dd = pd.DataFrame(dd,columns = ['Concepts', 'Descriptions'])

markdown_text = '''
## Descriptive analysis of research trend
National Institute of Justice provides a body of previous investigation of the effective way of 
improving criminal justice system in their collection [https://crimesolutions.ojp.gov]. 
'''
tabtitle = '''A Brief Look into Criminal Justice Research'''
    
app = dash.Dash()
server = app.server
app.title=tabtitle

app.layout = html.Div(children=[
    dcc.Markdown(children=markdown_text)
    ,
    dcc.Graph(
        id='publication_era',
        figure={
            'data': lis_treat,
            'layout':
            go.Layout(title='Agenda each decade (Not mutually exclusive)', barmode='group'),
            
        }
    ),
    dash_table.DataTable(
        id='timeline',
        data=dd.to_dict(orient='records'),
        columns=[{'id': c, 'name': c} for c in dd.columns],
        style_cell_conditional=[
             {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['Concepts', 'Descriptions']
        ],

        style_as_list_view=True,
     )
])


if __name__ == '__main__':
    app.run_server()
