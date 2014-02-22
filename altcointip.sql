CREATE TABLE IF NOT EXISTS `t_action` (
  `type` varchar(30) CHECK(`type` IN ('givetip','withdraw','info','register','accept','decline','history','redeem','rates')) NOT NULL,
  `state` varchar(30) CHECK(`state` in ('completed','pending','failed','declined','expired')) NOT NULL,
  `created_utc` integer NOT NULL,
  `from_user` varchar(30) NOT NULL,
  `to_user` varchar(30) DEFAULT NULL,
  `to_addr` varchar(34) DEFAULT NULL,
  `coin_val` float unsigned DEFAULT NULL,
  `fiat_val` float unsigned DEFAULT NULL,
  `txid` varchar(64) DEFAULT NULL,
  `coin` varchar(3) DEFAULT NULL,
  `fiat` varchar(3) DEFAULT NULL,
  `subreddit` varchar(30) DEFAULT NULL,
  `msg_id` varchar(30) NOT NULL,
  `msg_link` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`type`,`created_utc`,`msg_id`),
  UNIQUE (`msg_id`)
);

CREATE TABLE IF NOT EXISTS `t_addrs` (
  `username` varchar(30) NOT NULL,
  `network` varchar(30) NOT NULL,
  `coin` varchar(3) NOT NULL,
  `address` varchar(34) NOT NULL,
  PRIMARY KEY (`username`,`coin`),
  UNIQUE (`address`)
);

CREATE TABLE IF NOT EXISTS `t_users` (
  `username` varchar(30) NOT NULL,
  `network` varchar(30) NOT NULL,
  `joindate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `giftamount` float DEFAULT '0',
  PRIMARY KEY (`username`)
);

CREATE TABLE IF NOT EXISTS `t_values` (
  `param0` varchar(64) NOT NULL,
  `value0` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`param0`)
);
