import React from 'react';

import './Card.css';

export default class Card extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {
        return (
            <div className="col mb-4">
                <div className="card">
                    <img className="card-img-top img-fluid" src="https://d2ahiw9kb7is19.cloudfront.net/-/media/B3002A62D64F4EC6875E7B7AA344B7B6.jpg?d=20171117T100912&w=750" alt='Card image'></ img>
                    <div className="card-between">
                        <button type="button" class='add-plan'>
                            <div className='icon'>
                                <i className="fas fa-plus"></i>
                            </div>
                        </button>
                    </div>
                    <div className="card-body">
                        <h5 className="card-title">Senso-ji</h5>
                        <p className="card-text">Historic temple to the goddess of mercy</p>
                    </div>
                </div>
            </div>
        )
    }
}