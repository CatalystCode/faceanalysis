import * as React from 'react';
import * as Redux from 'redux';

// import { bindActionCreators, Dispatch } from 'redux';
// import { connect } from 'react-redux'
// import * as constants from '../constants';
// import * as store from '../store';

import './ImageViewer.css';

import { ImagePageProps, ImagePageState } from '../constants';

export class ImagePage extends React.Component<ImagePageProps,ImagePageState> {
  constructor(props: ImagePageProps){
    super(props);
  }

  public render() {
    return (
      <div className="img-right">
        <img src={this.props.subjectImage.url} height={this.props.subjectImage.height} 
          width={this.props.subjectImage.width} />
      </div>
    )
  }
}

// export const ImageViewer = (props: ImageProperties) => {
//   const img = new Image(props.height, props.width);
//   img.src = props.url;
  
//   return (
//     <div className="img-right">
//       <img src={img.src} height={img.height} width={img.width} />
//     </div>
//   )
// }




