SocialTipBot Twitter Development
============

In order to setup a workable and consistent development environment, a number of technologies are utilised.  
Of note the bot utilises Twitter webhooks for receiving of live notifications.

### Prereqisites
- Docker
- Docker-Compose
- Virtualenv
- ngrok
- Python3
- MySQL

### Technologies used by the bot:
- Twitter API
- Twitter Webhooks


### Docker images
Docker images are available from
[Reddcoin Docker on GitHub](https://github.com/reddcoin-project/reddcoin-docker/tree/master/tipbots)
Docker-Compose files are also available in the same repository

### MySQL configuration
Install and create a new MySQL database instance.
- run the included SQL file createDB.sql to create necessary database and user (edit the createDB.sql and update values accordingly).
- run the included SQL file altcointip.sql to create necessary tables.If you don't like to deal with command-line MySQL, use phpMyAdmin.

### Application configuration
The App will need to be running in order to complete all the configuration
- Setup a Virtualenv
  - Activate the environment
- Install prerequisites into the environment
  - pip3 install \
          dateutils==0.6.7 \
          irc==18.0.0 \
          mysqlclient==1.4.6 \
          praw==7.2.0 \
          PyYAML==5.3 \
          Jinja2==2.10.3
          SQLAlchemy==1.3.12
  - pip3 install https://github.com/reddcoin-project/python-twitter-webhooks/archive/master.zip
  - pip3 install https://github.com/ryanmcgrath/twython/archive/master.zip
  - EXPORT VERSION=0.1
  - pip3 install https://github.com/dpifke/pifkoin/archive/master.zip
- Run the server
  - cd src/
  - python ./run.py

The server should be running on localhost, listening on port 3000


## Twitter Configuration
The process of creating a Twitter bot
- Apply for a developer account
- Create a Twitter app
- Setup a development environment
- Link your Twitter app and dev environment
  - Generate keys and tokens
- Populate the values into the `src/conf/twitter/twitter.yml`
```yaml
    user: 'AccountName'
    app_key: 'app-key'
    app_secret: 'app-secret'
    oauth_token: 'oauth-token'
    oauth_token_secret: 'oauth-token-secret'
    envname: ''
    webhook_url: ''
    webhook_id: 
```
To configure the twitter webhook you will need to use ngrok to provide a receiving endpoint.
This endpoint provided by ngrok will be used in the configuration of the webhook.
```shell
  ./ngrok http 3000
```
With ngrok running, it will provide an output similar as:
```shell
  ngrok by @inconshreveable                                                                            (Ctrl+C to quit)
                                                                                                                   
  Session Status                online                                                                                 
  Account                       Developer (Plan: Free)                                                                 
  Update                        update available (version 2.3.38, Ctrl-U to update)                                    
  Version                       2.3.35                                                                                 
  Region                        United States (us)                                                                     
  Web Interface                 http://127.0.0.1:4040                                                                  
  Forwarding                    http://a4670d9e1b88.ngrok.io -> http://localhost:3000                                  
  Forwarding                    https://a4670d9e1b88.ngrok.io -> http://localhost:3000
```
Provide an envname, e.g. 'staging' and use the https value and amend the config file with the url:
```yaml
  envname: 'staging'
  webhook_url: 'https://a4670d9e1b88.ngrok.io/webhooks/twitter'
  webhook_id: 
```
finally the configuration of webhook is done using the scripts supplied in `src/utils`

First to create the configuration.  
From the `src/` directory
```shell
  cd src/
  python utils/create-twitter-webhook.py
```
Result:
```shell
  {
      "created_timestamp": "2021-03-30 03:08:52 +0000",
      "id": "1376733430682531138",
      "url": "https://a4670d9e1b88.ngrok.io/webhooks/twitter",
      "valid": true
  }
```
Next, your account will need to subscribe to the webhook
```shell
  python utils/subscribe-twitter-webhook.py
```
Result:
```shell
{
    "environments": [
        {
            "environment_name": "staging",
            "webhooks": [
                {
                    "created_timestamp": "2021-03-30 03:08:52 +0000",
                    "id": "1376733430682531138",
                    "url": "https://a4670d9e1b88.ngrok.io/webhooks/twitter",
                    "valid": true
                }
            ]
        }
    ]
}
```
