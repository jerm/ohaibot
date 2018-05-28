# Description

            Welcome to the Offite Halla Audiovisual Interface Robot, or OhaiBot

            This is the sofware repo for my ![absurd contraption](https://www.youtube.com/watch?v=c0bsKc4tiuY)

# Installation

            clone the repo

            $ cd ohaibot

            $ sudo pip install --user -r requirements.txt

            # edit ohaibot.ini

            # edit zappa_setting.json

            $ zappa deploy 

            # set up slack slash command


# Edit ohaibot.ini
        queue names!
        angles!
        oh my!

# Edit api.ini
        queue names!
        users!
        oh my!

# Usage

        $ sudo python ohaibot.py 

        # Test your setup
        ## Start the dev server
        ./api.py

        ## Send a sample query
        curl http://localhost:5000/ohai --data-binary @example-request.json

        ## Run the Robot Software
        sudo python ohaibot.py

