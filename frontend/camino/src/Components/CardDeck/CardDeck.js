import React from 'react';

import Card from '../Card/Card'
import './CardDeck.css';

export default class CardDeck extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {
        return (
            <div className="container-fluid">
                <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4">
                    <Card />
                    <Card />
                    <Card />
                    <Card />
                    <Card />
                </div>
            </div>
        )
    };
}
