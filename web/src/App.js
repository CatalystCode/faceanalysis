import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

import { browserHistory } from 'react-router';
import { BrowserRouter as Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import MainPage from './components/MainPage';
import configureStore from './redux/configureStore';


const store = configureStore(window.__STATE__);

class App extends Component {
  render() {
    return (
      <div className="App">
        <header className="App-header">
        </header>
        <Provider store={store}>
          {/* <Router history={browserHistory}> */}
            <MainPage />
          {/* </Router> */}
        </Provider>,
      </div>
    );
  }
}

export default App;
