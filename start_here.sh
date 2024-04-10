#!/bin/bash
# Enable poetry if not running inside docker and poetry is installed
if [[ $HOSTNAME != "docker-"* ]] && (hash poetry 2>/dev/null); then
    run_command="poetry run"
fi

conferences=(
    # "aaai 2017 old_style no_subpage"
    # "aaai 2018 old_style no_subpage"
    # "aaai 2019 no_subpage"
    # "aaai 2020"
    # "aaai 2021"
    # "aaai 2022"
    # "aaai 2023"
    "aaai 2024"
    # "acl 2017"
    # "acl 2018"
    # "acl 2019"
    # "acl 2020"
    # "acl 2021"
    # "acl 2022"
    # "acl 2023"
    # coling happens on even years
    # "coling 2018"
    # "coling 2020"
    # "coling 2022"
    # "cvpr 2017 no_subpage"
    # "cvpr 2018"
    # "cvpr 2019"
    # "cvpr 2020"
    # "cvpr 2021"
    # "cvpr 2022"
    # "cvpr 2023"
    # "eacl 2017"
    # "eacl 2021"
    # "eacl 2023"
    # "eacl 2024"
    # eccv happens on even years
    # "eccv 2018"
    # "eccv 2020"
    # "eccv 2022"
    # "emnlp 2017"
    # "emnlp 2018"
    # "emnlp 2019"
    # "emnlp 2020"
    # "emnlp 2021"
    # "emnlp 2022"
    # "emnlp 2023"
    # "findings 2020"
    # "findings 2021"
    # "findings 2022"
    # "findings 2023"
    # "findings 2024"
    # iccv happens on odd years
    # "iccv 2017 no_subpage"
    # "iccv 2019"
    # "iccv 2021"
    # "iccv 2023"
    # "iclr 2018"
    # "iclr 2019"
    # "iclr 2020"
    # "iclr 2021"
    # "iclr 2022"
    # "iclr 2023"
    # "icml 2017"
    # "icml 2018"
    # "icml 2019"
    # "icml 2020"
    # "icml 2021"
    # "icml 2022"
    # "icml 2023"
    # "ijcai 2017"
    # "ijcai 2018"
    # "ijcai 2019"
    # "ijcai 2020"
    # "ijcai 2021"
    # "ijcai 2022"
    # "ijcai 2023"
    # "ijcnlp 2017"
    # "ijcnlp 2019"
    # "ijcnlp 2021"
    # "ijcnlp 2022"
    # "kdd 2017"
    # "kdd 2018"
    # "kdd 2020"
    # "kdd 2021"
    # "kdd 2022"
    # "kdd 2023"
    # "naacl 2018"
    # "naacl 2019"
    # "naacl 2021"
    # "naacl 2022"
    # "neurips 2017"
    # "neurips 2018"
    # "neurips 2019"
    # "neurips 2020"
    # "neurips 2021"
    # "neurips 2022"
    # "neurips 2023"
    # "neurips_workshop 2019"
    # "neurips_workshop 2020"
    # "neurips_workshop 2021"
    # "neurips_workshop 2022"
    # "sigchi 2018"
    # "sigchi 2019"
    # "sigchi 2020"
    # "sigchi 2021"
    # "sigchi 2022"
    # "sigchi 2023" # TODO
    # "sigdial 2017"
    # "sigdial 2018"
    # "sigdial 2019"
    # "sigdial 2020"
    # "sigdial 2021"
    # "sigdial 2022"
    # "sigdial 2023"
    # "tacl 2017"
    # "tacl 2018"
    # "tacl 2019"
    # "tacl 2020"
    # "tacl 2021"
    # "tacl 2022"
    # "tacl 2023"
    # "wacv 2020 no_subpage"
    # "wacv 2021 no_subpage"
    # "wacv 2022 no_subpage"
    # "wacv 2023 no_subpage"
    # "wacv 2024 no_subpage"
)

# update_papers_with_code=1

acl_conferences=(
    "acl"
    "coling"
    "eacl"
    "emnlp"
    "findings"
    "ijcnlp"
    "naacl"
    "sigdial"
    "tacl"
)

abstract_only_conferences=(
    "kdd"
    "sigchi"
)

for conference in "${conferences[@]}"; do
    conf_year=($conference)

    # download papers' informations and pdfs
    echo -e "\nScrapping information for ${conf_year[0]} ${conf_year[1]}"
    if [[ ${conf_year[0]} == "aaai" ]]; then
        if [ "${#conf_year[@]}" -eq 4 ]; then
            $run_command scrapy crawl aaai -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]} -a new_style=False -a subpage=False
        elif [ "${#conf_year[@]}" -eq 3 ]; then
            $run_command scrapy crawl aaai -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]} -a subpage=False
        else
            $run_command scrapy crawl aaai -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
        fi
    elif [[ " ${acl_conferences[*]} " =~ " ${conf_year[0]} " ]]; then
        $run_command scrapy crawl acl -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
    elif [[ ${conf_year[0]} == "cvpr" ]] || [[ ${conf_year[0]} == "iccv" ]] || [[ ${conf_year[0]} == "wacv" ]]; then
        if [ "${#conf_year[@]}" -eq 3 ]; then
            $run_command scrapy crawl thecvf -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]} -a subpage=False
        else
            $run_command scrapy crawl thecvf -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
        fi
    elif [[ ${conf_year[0]} == "iclr" ]] || [[ ${conf_year[0]} == "neurips_workshop" ]] || ([[ ${conf_year[0]} == "neurips" ]] && [[ ${conf_year[1]} == "2022" ]]) \
        || ([[ ${conf_year[0]} == "neurips" ]] && [[ ${conf_year[1]} == "2023" ]]); then
        $run_command python openreview_scrapper.py -c ${conf_year[0]} -y ${conf_year[1]} -d
    elif [[ ${conf_year[0]} == "icml" ]]; then
        $run_command scrapy crawl mlr_press -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
    else # eccv, ijcai, or neurips
        $run_command scrapy crawl ${conf_year[0]} -s LOG_LEVEL=INFO -a year=${conf_year[1]}
    fi
done

if [ -n "$update_papers_with_code" ]; then
    mkdir -p data/papers_with_code
    wget https://paperswithcode.com/media/about/papers-with-abstracts.json.gz -P data/papers_with_code
    wget https://paperswithcode.com/media/about/links-between-papers-and-code.json.gz -P data/papers_with_code
    gunzip -f data/papers_with_code/papers-with-abstracts.json.gz
    gunzip -f data/papers_with_code/links-between-papers-and-code.json.gz
fi
