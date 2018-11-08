import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { getImages } from '../redux/actions/images';

let createHandlers = function(dispatch) {
  let onLoad = function(node, data) {
    dispatch(getImages(data))
  };

  return {
    onLoad,
    // other handlers
  };
}


class MainPage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      data: [],
      subjectImage: {},
      targetImage : {},
      candidateImages: [],
      hasErrored: false,
      isLoading: false,
      appData: {}
    };
    this.handlers = createHandlers(this.props.dispatch);
    // this.handler = this.handler.bind(this); 
  }

  componentDidMount() {
    // fetch the data...
    this.handlers.onLoad();
    // this.props.store.dispatch(getImages())
  }

  handler(val) {
    // this.props.action();
  }

  render() {
    this.handlers.onLoad();
    return (
      <div>
        <div>TBD</div>
        {/* <PageTop>
                    <--Menu />
                </PageTop> */}
        {/* <Routes  action={this.handler}  /> */}
        {/* <Footer /> */}
      </div>
    );
  }
}

MainPage.defaultProps = {};
// MainPage.propTypes = {};

const mapStateToProps = (state) => {
  return {
    data: state.images.data, // object of meta and URI
    // targetImage: state.images.targetImage.data, // object of meta and URI
    // candidateImages: state.images.candidateImages.data, // an array
    hasErrored: state.images.hasErrored,
    isLoading: state.images.isLoading,
    errorMessage: state.images.errorMessage
  };
};

// export default connect(mapStateToProps,
//   { getImages })(MainPage);

export default connect()(MainPage);
