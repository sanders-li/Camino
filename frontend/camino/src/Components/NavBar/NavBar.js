import React from 'react';
import './NavBar.css';

export default class NavBar extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {
        return (
            <nav className="navbar navbar-expand-md navbar-dark bg-dark sticky-top">
                <div className='container-fluid'>
                    <a href="#">
                        <div class='navbar-brand d-flex'>
                            <img src="./logo.png" class="d-inline-block align-top" alt=""></ img>
                            Camino            
                        </div>
                    </a>
                    <div className="navbar-form mr-auto w-75">
                        <form action="/" method="POST">
                            <div className="input-group">
                                <input id = 'autocomplete' class="form-control mr-sm-2" type="search" name="city" id="city" placeholder="Where do you want to go?"></ input>
                                <div className="input-group-append">
                                    <button className="btn btn-info" type="submit">
                                        <i className="fas fa-search"></i>
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div className="navbar navbar-icon">
                        <div className="plan-icon" id="sidebarExpand">
                            <button type="button" class="btn btn-info">
                                <i className="fas fa-suitcase"></i>
                            </button>
                            <div className='plan-events'>1</div>
                        </div>
                    </div>
                </div>
            </nav>
        )
    };
}