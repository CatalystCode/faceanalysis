import * as React from 'react';
import './App.css';

// import logo from './logo.svg';

import { ImageViewer } from './components/ImageViewer';

class App extends React.Component {
  public render() {
    return (
      <div className="App">
        <header className="App-header">
          {/* <img src={logo} className="App-logo" alt="logo" />
          <h2 className="App-title">Welcome to React</h2> */}
        </header>
        <div className="App-intro">
          <ImageViewer url={"https://images.pexels.com/photos/736716/pexels-photo-736716.jpeg"} 
            height={200} width={300} />
        </div>
      </div>
    );
  }
}

export default App;
