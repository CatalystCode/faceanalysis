import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { getImages } from '../redux/actions/images';

class MainPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
          appData : {}
        };
        // this.handler = this.handler.bind(this);
    }

    componentDidMount(){
      // fetch the data...
      this.props.getImages();
    }

    handler(val) {
        // this.props.action();
    }

    render() {
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
MainPage.propTypes = {};

const mapStateToProps = (state) => {
  return {
      subjecImage: state.images.data, // object of meta and URI
    //   targetImage: state.images.targetImage.data, // object of meta and URI
    //   candidateImages: state.images.candidateImages.data, // an array
      hasErrored: state.images.hasErrored,
      isLoading: state.images.isLoading,
      errorMessage: state.images.errorMessage
  };
};

export default connect(mapStateToProps,
    { getImages} )(MainPage);

// export default MainPage;


// export interface ImageProperties {
//     url: string;
//     alt?: string;
//     width: number;
//     height: number
//   }
