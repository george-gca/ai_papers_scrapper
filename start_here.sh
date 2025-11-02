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
    # "aaai 2024"
    # "aaai 2025"
    # "acl 2017"
    # "acl 2018"
    # "acl 2019"
    # "acl 2020"
    # "acl 2021"
    # "acl 2022"
    # "acl 2023"
    # "acl 2024"
    # "acl 2025"
    # "aistats 2017"
    # "aistats 2018"
    # "aistats 2019"
    # "aistats 2020"
    # "aistats 2021"
    # "aistats 2022"
    # "aistats 2023"
    # "aistats 2024"
    # "aistats 2025"
    # "coling 2018"
    # "coling 2020"
    # "coling 2022"
    # "coling 2024"
    # "coling 2025"
    # "cvpr 2017 no_subpage"
    # "cvpr 2018"
    # "cvpr 2019"
    # "cvpr 2020"
    # "cvpr 2021"
    # "cvpr 2022"
    # "cvpr 2023"
    # "cvpr 2024"
    # "cvpr 2025"
    # "eacl 2017"
    # "eacl 2021"
    # "eacl 2023"
    # "eacl 2024"
    # eccv happens on even years
    # "eccv 2018"
    # "eccv 2020"
    # "eccv 2022"
    # "eccv 2024"
    # "emnlp 2017"
    # "emnlp 2018"
    # "emnlp 2019"
    # "emnlp 2020"
    # "emnlp 2021"
    # "emnlp 2022"
    # "emnlp 2023"
    # "emnlp 2024"
    "emnlp 2025"
    # "findings 2020"
    # "findings 2021"
    # "findings 2022"
    # "findings 2023"
    # "findings 2024"
    # "findings 2025"
    # iccv happens on odd years
    # "iccv 2017 no_subpage"
    # "iccv 2019"
    # "iccv 2021"
    # "iccv 2023"
    # "iccv 2025"
    # "iclr 2017"
    # "iclr 2018"
    # "iclr 2019"
    # "iclr 2020"
    # "iclr 2021"
    # "iclr 2022"
    # "iclr 2023"
    # "iclr 2024"
    # "iclr 2025"
    # "icml 2017"
    # "icml 2018"
    # "icml 2019"
    # "icml 2020"
    # "icml 2021"
    # "icml 2022"
    # "icml 2023"
    # "icml 2024"
    # "icml 2025"
    # "ijcai 2017"
    # "ijcai 2018"
    # "ijcai 2019"
    # "ijcai 2020"
    # "ijcai 2021"
    # "ijcai 2022"
    # "ijcai 2023"
    # "ijcai 2024"
    # "ijcai 2025"
    # "ijcnlp 2017"
    # "ijcnlp 2019"
    # "ijcnlp 2021"
    # "ijcnlp 2022"
    # "ijcnlp 2023"
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
    # "naacl 2024"
    # "naacl 2025"
    # "neurips 2017"
    # "neurips 2018"
    # "neurips 2019"
    # "neurips 2020"
    # "neurips 2021"
    # "neurips 2022"
    # "neurips 2023"
    # "neurips 2024"
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
    # "sigdial 2024"
    "sigdial 2025"
    # "siggraph 2017"
    # "siggraph 2018"
    # "siggraph 2019"
    # "siggraph 2020"
    # "siggraph 2021"
    # "siggraph 2022"
    # "siggraph 2023"
    # "siggraph 2024"
    # "siggraph 2025"
    # "siggraph-asia 2017"
    # "siggraph-asia 2018"
    # "siggraph-asia 2019"
    # "siggraph-asia 2020"
    # "siggraph-asia 2021"
    # "siggraph-asia 2022"
    # "siggraph-asia 2023"
    # "siggraph-asia 2024"
    # "tacl 2017"
    # "tacl 2018"
    # "tacl 2019"
    # "tacl 2020"
    # "tacl 2021"
    # "tacl 2022"
    # "tacl 2023"
    # "tacl 2024"
    # "tacl 2025"
    # "uai 2019"
    # "uai 2020"
    # "uai 2021"
    # "uai 2022"
    # "uai 2023"
    # "uai 2024"
    # "wacv 2020 no_subpage"
    # "wacv 2021 no_subpage"
    # "wacv 2022 no_subpage"
    # "wacv 2023 no_subpage"
    # "wacv 2024 no_subpage"
    # "wacv 2025 no_subpage"
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
    elif [[ ${conf_year[0]} == "siggraph" ]] || [[ ${conf_year[0]} == "siggraph-asia" ]]; then
        $run_command scrapy crawl siggraph -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
    elif [[ " ${acl_conferences[*]} " =~ " ${conf_year[0]} " ]]; then
        $run_command scrapy crawl acl -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
    elif [[ ${conf_year[0]} == "cvpr" ]] || [[ ${conf_year[0]} == "iccv" ]] || [[ ${conf_year[0]} == "wacv" ]]; then
        if [ "${#conf_year[@]}" -eq 3 ]; then
            $run_command scrapy crawl thecvf -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]} -a subpage=False
        else
            $run_command scrapy crawl thecvf -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
        fi
    elif [[ ${conf_year[0]} == "aistats" ]] || [[ ${conf_year[0]} == "icml" ]] || [[ ${conf_year[0]} == "uai" ]]; then
        $run_command scrapy crawl mlr_press -s LOG_LEVEL=INFO -a conference=${conf_year[0]} -a year=${conf_year[1]}
    elif [[ ${conf_year[0]} != "iclr" ]]; then # eccv, ijcai, or neurips
        $run_command scrapy crawl ${conf_year[0]} -s LOG_LEVEL=INFO -a year=${conf_year[1]}
    fi

    case "${conf_year[0]}" in
        aaai|acl|aistats|coling|eacl|eccv|emnlp|iclr|icml|ijcai|ijcnlp|kdd|naacl|neurips|sigchi|sigdial|uai ) is_openreview_conference=1;;
        *) is_openreview_conference=0;;
    esac

    if [ $is_openreview_conference -eq 1 ]; then
        echo ""
        $run_command python openreview_scrapper.py -c ${conf_year[0]} -y ${conf_year[1]} -w -d
    fi

done

if [ -n "$update_papers_with_code" ]; then
    mkdir -p data/papers_with_code
    wget https://paperswithcode.com/media/about/papers-with-abstracts.json.gz -P data/papers_with_code
    wget https://paperswithcode.com/media/about/links-between-papers-and-code.json.gz -P data/papers_with_code
    gunzip -f data/papers_with_code/papers-with-abstracts.json.gz
    gunzip -f data/papers_with_code/links-between-papers-and-code.json.gz
fi
