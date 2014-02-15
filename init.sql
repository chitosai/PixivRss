-- phpMyAdmin SQL Dump
-- version 2.10.3
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Feb 15, 2014 at 07:51 AM
-- Server version: 5.0.51
-- PHP Version: 5.2.6

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

-- 
-- Database: `pixiv_rss`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `pixiv_weibo_id_map`
-- 

CREATE TABLE `pixiv_weibo_id_map` (
  `pixiv_uid` int(8) NOT NULL,
  `weibo_uid` varchar(32) NOT NULL,
  PRIMARY KEY  (`pixiv_uid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Pixiv_id与Weibo_id的映射表';
