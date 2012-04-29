#!/bin/bash
#cd /home/apps/filmasterpl/filmaster-stable
set -x
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
python run_recom_new_users.py
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
./run_compute_probable_scores2.sh
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
python run_popularity.py
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
python run_fetch_synopses_daily.py
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
./run_compute_film_comparators.sh
NOW=$(date +"%y-%m-%d-%H-%M")
#echo $NOW
#bin/daily_updates.sh
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
./run_amazonka_import.sh
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
./run_amazonka_export.sh
NOW=$(date +"%y-%m-%d-%H-%M")

