import React from 'react';
import {
    BrowserRouter as Router,
    Switch,
    Route,
    Link
} from "react-router-dom"

import NavBar from '../NavBar/NavBar'
import Banner from '../Banner/Banner'
import CardDeck from '../CardDeck/CardDeck'

import './App.css'

export default class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            searchResults: [],
            location: [],
            inventory: []
        };
    };

    render() {
        return (
            <div>
                <NavBar onSearch={this.search} />
                <Banner location={this.location} />
                <CardDeck location={this.location} />
            </div>
        )
    };
}