import * as React from 'react';
import { bindActionCreators, Dispatch } from 'redux';
import { connect } from 'react-redux'
import * as constants from '../constants';
import * as store from '../store';

import './ImageViewer.css';

import { ImageProperties } from '../constants';
// https://github.com/piotrwitek/react-redux-typescript-guide#typing-connect
const mapStateToProps = (state: Types.RootState, ownProps: SFCCounterProps) => ({
  count: state.counters.reduxCounter,
});



export const ImageViewer = (props: ImageProperties) => {
  // store.subscribe();
  const img = new Image(props.height, props.width);
  img.src = props.url;
  
  return (
    <div className="img-right">
      <img src={img.src} height={img.height} width={img.width} />
    </div>
  )
}

