from app import app
from mongoDocuments import Config, Result

from dash.dependencies import Input, Output, State, ALL
import pandas as pd


@app.callback(
    [Output('CommitSlider', 'marks'),
     Output('CommitSlider', 'value'),
     Output('CommitSlider', 'max'),
     Output('SliderDict', 'data')],
    [Input('refreshButton', 'n_clicks')])
def _setSliderLabels(refreshClicks):
    print(f'\n[CALLBACK] refreshing commit list for {refreshClicks}th time')

    uniqueSHAs = Config.objects().distinct(field='commitSHA')
    print(f'\tFound {len(uniqueSHAs)} unique SHAs')
    options = pd.DataFrame(columns=['SHA', 'CommitDate'])

    for sha in uniqueSHAs:
        c = Config.objects(commitSHA=sha).first()
        options = options.append({'SHA': sha, 'CommitDate': c.commitDate, 'commitMessage': c.commitMessage},
                                 ignore_index=True)

    options = options.sort_values('CommitDate')

    marks = {}
    for i, o in enumerate(options.iterrows()):
        message = o[1].commitMessage.replace('\n', ' ')
        marks[i] = f'{o[1].SHA[0:6]} {message}'
    return marks, [len(marks) - 5, len(marks) - 1], len(marks) - 1, options.to_json()


@app.callback(
    Output('SliderSpeedups', 'data'),
    [Input('CommitSlider', 'value'),
     Input('SliderDict', 'data')],
)
def _updateManyLinePlot(sliderPos, sliderDict):
    print('\n[CALLBACK] Updating Many Line')

    low_i = sliderPos[0]
    high_i = sliderPos[1]

    parsedSlider = pd.read_json(sliderDict)
    baseCommit = parsedSlider.iloc[low_i]

    for i in range(low_i, high_i + 1):
        print(parsedSlider.iloc[i])

    return parsedSlider.to_json()