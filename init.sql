-- phpMyAdmin SQL Dump
-- version 3.4.10.1deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jun 27, 2014 at 06:13 AM

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `pixiv_rss`
--

-- --------------------------------------------------------

--
-- Table structure for table `award_log`
--

CREATE TABLE `award_log` (
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上榜时间',
  `type` tinyint(4) NOT NULL,
  `uid` int(11) NOT NULL COMMENT '上榜用户pixiv_id'
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `pixiv_weibo_id_map`
--

CREATE TABLE `pixiv_weibo_id_map` (
  `pixiv_uid` int(8) NOT NULL,
  `weibo_uid` varchar(32) NOT NULL,
  PRIMARY KEY (`pixiv_uid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Pixiv_id与Weibo_id的映射表';
