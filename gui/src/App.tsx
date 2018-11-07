import * as React from 'react';
import './App.css';

// import logo from './logo.svg';

import { ImagePage } from './components/ImageViewer';

class App extends React.Component {
  public render() {
    return (
      <div className="App">
        <header className="App-header">
          {/* <img src={logo} className="App-logo" alt="logo" />
          <h2 className="App-title">Welcome to React</h2> */}
        </header>
        <div className="App-intro">
          <ImagePage {...} />
        </div>
      </div>
    );
  }
}

export default App;
