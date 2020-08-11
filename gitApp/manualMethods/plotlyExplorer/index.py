from app import *
from layout import makeLayout

app.layout = makeLayout()

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

