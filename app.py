##### import libraries #####
import pandas as pd
import requests
import xmltodict
import plotly.express as px
from dash import Dash, dcc, html, Input, Output,callback
import geopandas as gpd

### load xml file from url and convert to dictionary "Gesamtergebnisse" ###
# load overall results
response = requests.get('https://www.bundeswahlleiterin.de/bundestagswahlen/2021/ergebnisse/opendata/daten/gesamtergebnis_05.xml')
xml_overallresults = xmltodict.parse(response.content)

### vote 2021 ###
# create list with all parties
parties = []

for i in range(4,11):
    parties.append(xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][0]['Gruppenergebnis'][i]['@Name'])

# create list with all secondvote results
secondvote = []

for i in range(4,11):
    secondvote.append(xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][0]['Gruppenergebnis'][i]['Stimmergebnis'][1]['@Prozent'])

secondvote = [float(i) for i in secondvote]

# calculate votes for others
other_secondvote = (100-sum(secondvote))

# add SSW to data
parties.append('SSW')
secondvote.append(0.1)

# append other to the lists
parties.append('Sonstige')
secondvote.append(other_secondvote)

# create dataframe from lists
data = pd.DataFrame({'Partei':parties, 'Zweitstimme':secondvote})

# round dataframe by 2 decimal places
data = data.round(2)

# sort dataframe by second vote
data = data.sort_values(by='Zweitstimme', ascending=False)

# move row 'Sonstige' to the end and reset index
data = data._append(data.loc[data['Partei'] == 'Sonstige'])
data = data.reset_index(drop=True)

# delete row with index 5 'Sonstiges'
data = data.drop(5)

### Create graph of Partys second vote ###
fig_secondvote = px.bar(data, x='Partei', y='Zweitstimme', title='Ergebnisse Bundestagswahl 2021',
                        color='Partei',
                        color_discrete_map={
                                            'CDU': '#32302e',
                                            'SPD': '#e3000f',
                                            'GRÜNE': '#64a12d',
                                            'DIE LINKE': '#b61c3e',
                                            'FDP': '#ffed00',
                                            'AfD': '#009ee0',
                                            'Sonstige': '#adb9ca',
                                            'CSU': '#0080c9',
                                            }, text_auto=True)

# adjust graph size
fig_secondvote.update_yaxes(range=[0, max(data['Zweitstimme']) * 1.15])

# remove legend
for trace in fig_secondvote.data:
    trace.showlegend = False

# add text to graph
fig_secondvote.update_traces(textposition='outside')

# add % to graph
fig_secondvote.for_each_trace(lambda t: t.update(texttemplate = t.texttemplate + ' %'))

#add source
fig_secondvote.add_annotation(
    text='Quelle: © Der Bundeswahlleiter, Wiesbaden 2021',
    x=0, y=-0.15,
    xref='paper', yref='paper',
    showarrow=False,
    font=dict(size=10, color='gray')
)

### own district research ###
# create list with districts
district = []

for i, result in enumerate(xml_overallresults['Gesamtergebnis']['Gebietsergebnis']):
    gebiet_text = result['GebietText']
    district.append(gebiet_text)

district = district[17:]

# add district number to districtlist
district_with_number = [f'{i + 1} - {item}' for i, item in enumerate(district)]

# dict with district number
district_number = {element: num for num, element in enumerate(district_with_number, start=17)}

### create map ###
# load shapefile
shapefile_path = 'data/btw21_geometrie_wahlkreise_vg250_shp/Geometrie_Wahlkreise_20DBT_VG250.shp'

# convert shapefile to geodataframe
gdf = gpd.read_file(shapefile_path)

# convert to epsg 4326
gdf = gdf.to_crs(epsg=4326)

# create map
fig_map = px.choropleth_mapbox(
    gdf,
    geojson=gdf.geometry,
    locations='WKR_NR',
    mapbox_style="carto-positron",
    center={"lat": 51.1, "lon": 10},
    zoom=3.9,
    opacity=0.1,
    labels={'WKR_NR': 'Wahlkreisnummer '},
    title='Wahlkreiskarte'
)

# remove legend
fig_map.for_each_trace(lambda t: t.update(showlegend=False))

# Add source
fig_map.add_annotation(
    text='Quelle: © Der Bundeswahlleiter, Statistisches Bundesamt, Wiesbaden 2020,'
         '<br>Wahlkreiskarte für die Wahl zum 20. Deutschen Bundestag'
         '<br>Grundlage der Geoinformationen © Geobasis-DE / BKG 2020',
    x=0, y=-0.18,
    xref='paper', yref='paper',
    showarrow=False,
    align='left',
    font=dict(size=10, color='gray')
)

##### create dash app ##### create dash website ######
app = Dash()

### Website Layout ###
app.layout = html.Div([
    # Headline
    html.H1(children='Wie wählt Dein Bezirk?',
            style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 20}),
    # introduction
    html.P(children='''Jeder weiß, wie die Bundestagswahl ausgegangen ist. Aber weißt Du auch, wie Dein Bezirk gewählt hat?
                        Hier kannst Du es herausfinden.
                        Noch mal kurz als Erinnerung, wie es 2021 auf Bundesebene ausgegangen ist:''',
            ),
    # graph secondvote
    dcc.Graph(figure=fig_secondvote),
    # summary 2021
    html.P(children='''Im Jahr 2021 geht die SPD als Wahlsieger heraus. Zusammen mit den Grünen und der FDP gründen sie die erste Ampelkoalition
    in der Geschichte der Bundesrepublik Deutschland. Die Union geht dabei als klarer Verlieren aus der Wahl heraus. Die Linke schafft es gerade so durch 
    drei Direktmandate in den Bundestag und die AfD gewinnt weiter an Zuspruch. Eine weitere Besonderheit ist der Südschleswigsche Wählerverband (SSW), 
    der durch die Vertretung einer nationalen Minderheit nach 1961 wieder in den Bundestag einzieht.''',
            ),
    # headline own district
    html.H1(children='Wahlergebnisse in Deinem Wahlkreis',
            ),
    # short guide
    html.P(children='''Und jetzt zurück zu Deinem Wahlbezirk. Du weißt nicht, in welchem Wahlbezirk du wohnst?
                        Keine Sorge - auf der Karte kannst du deinem Wahlbezirk herausfinden. 
                        Danach kannst du deinen Wahlbezirk im Menü unter der Karte auswählen. Wenn du deinen Wahlkreis
                        doch kennst, dann kannst du ihn auch einfach unten eingeben.''',
            ),
    # disctrict map
    dcc.Graph(figure=fig_map,
              style={'margin': '10px 20% 10px 20%'}
              ),
    # dropdown district
    dcc.Dropdown(district_with_number, id='dropdown-district', placeholder="Gib hier Deinen Wahlkreis ein.",
          ),
    # automated text
    html.P(id='selected-district-output2021',
            style={'align': 'left'}
           ),
    # graph for district
    dcc.Graph(id='graph-district')
])

### Dropdown for districts ###
# Start app callback for dropdown
@callback(
    [Output('selected-district-output2021', 'children'),
     Output('graph-district', 'figure')],
    Input('dropdown-district', 'value'),
    prevent_initial_call=True
)

# Define outputfunction for dropdown-text
def update_ouput(selected_district):
    # create list with district candidates
    district_candidate = []
    for i in range(4, 9):
        district_candidate.append(xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][int(district_number[(selected_district)])]['Gruppenergebnis'][i]['@Direktkandidat'])
    # turn lastname and surname
    district_candidate = [name.split(', ')[1] + ' ' + name.split(', ')[0] for name in district_candidate]
    #create list with district parties
    district_party = []
    for i in range(4, 9):
        district_party.append(
            xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][int(district_number[(selected_district)])][
                'Gruppenergebnis'][i]['@Name'])
    # create list with district percentage of candidates
    district_percentage = []
    for i in range(4, 9):
        district_percentage.append(
            xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][int(district_number[(selected_district)])][
                'Gruppenergebnis'][i]['Stimmergebnis'][0]['@Prozent'])
    district_percentage = [float(i) for i in district_percentage]
    # create dataframe for district selected; sort, round and reset index
    data_district = pd.DataFrame(
        {'Name': district_candidate, 'Partei': district_party, 'Direktstimmen': district_percentage})
    data_district = data_district.sort_values(by='Direktstimmen', ascending=False)
    data_district = data_district.round(2)
    data_district = data_district.reset_index(drop=True)
    # rename GRÜNEN
    data_district['Partei'] = data_district['Partei'].replace({'GRÜNE': 'BÜNDNIS 90/DIE GRÜNEN'})
    # print winner text
    automated_text_winner = f'Im Wahlkreis {selected_district} hat {data_district.loc[0,"Name"]} von der Partei \u201E{data_district.loc[0,"Partei"]}" mit {data_district.loc[0,"Direktstimmen"]} % der Stimmen gewonnen.'
    # get voterturnout
    voterturnout = xml_overallresults['Gesamtergebnis']['Gebietsergebnis'][int(district_number[(selected_district)])]['Gruppenergebnis'][1]['Stimmergebnis']['@Prozent']
    voterturnout = round(float(voterturnout), 2)
    automated_text_voterturnout = f' Die Wahlbeteiligung lag 2021 in diesem Wahlbezirk bei {voterturnout} %.'
    # calculate difference between first and second candidate
    difference = data_district.loc[0, "Direktstimmen"] - data_district.loc[1, "Direktstimmen"]
    # if diffrence bigger than 8% print far text elif pring close text else print normal text
    if difference > 8:
        automated_text_second = f' Mit einem großen Abstand von {difference: .2f} % auf dem zweiten Platz ist {data_district.loc[1, "Name"]} von der Partei \u201E{data_district.loc[1, "Partei"]}" mit {data_district.loc[1, "Direktstimmen"]} % .'
    elif difference > 3:
        automated_text_second = f' Auf dem zweiten Platz dahinter ist {data_district.loc[1, "Name"]} von der Partei \u201E{data_district.loc[1, "Partei"]}" mit {data_district.loc[1, "Direktstimmen"]} % der Stimmen.'
    else:
        automated_text_second = f' Knapp dahinter mit einer Differenz von {difference: .2f} % auf dem zweiten Platz ist {data_district.loc[1, "Name"]} von der Partei \u201E{data_district.loc[1, "Partei"]}" mit {data_district.loc[1, "Direktstimmen"]} % der Stimmen.'
    automated_text = automated_text_winner + automated_text_voterturnout + automated_text_second
    # create graph for district
    fig_district = px.bar(data_district, x='Partei', y='Direktstimmen', title='Ergebnisse Bundestagswahl 2021 in deinem Wahlkreis',
                            color='Partei',
                            color_discrete_map={
                                'CDU': '#32302e',
                                'SPD': '#e3000f',
                                'BÜNDNIS 90/DIE GRÜNEN': '#64a12d',
                                'DIE LINKE': '#b61c3e',
                                'FDP': '#ffed00',
                                'AfD': '#009ee0',
                                'Sonstige': '#adb9ca',
                                'CSU': '#0080c9',
                            }, text_auto=True)

    # adjust graph size
    fig_district.update_yaxes(range=[0, max(data_district['Direktstimmen']) * 1.15])

    # remove legend
    for trace in fig_district.data:
        trace.showlegend = False

    # add text to graph
    fig_district.update_traces(textposition='outside')

    # add % to graph
    fig_district.for_each_trace(lambda t: t.update(texttemplate=t.texttemplate + ' %'))

    # add annotation for district graph
    fig_district.add_annotation(
        text='Quelle: © Der Bundeswahlleiter, Wiesbaden 2021',
        x=0, y=-0.15,
        xref='paper', yref='paper',
        showarrow=False,
        font=dict(size=10, color='gray')
    )
    return automated_text, fig_district

### Run Dash ###
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
