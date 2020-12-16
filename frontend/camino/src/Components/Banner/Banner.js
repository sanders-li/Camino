import React from 'react';
import './Banner.css';

export default class Banner extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {
        return(
            <div class="jumbotron">
                <div class="container banner-text">
                    <h1 class="display-4">Tokyo, Japan</h1>
                    <p class="lead">Japan’s busy capital, Tokyo mixes the ultramodern and the traditional, from neon-lit skyscrapers to historic temples.</p>
                </div>
            </div>
        )
    }
}