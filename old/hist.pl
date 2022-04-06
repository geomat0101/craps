#!/usr/bin/env perl

my(%hist);

while (<>)
{
	chomp();
	my($bucket) = int($_ / 100);
	if(exists($hist{$bucket}))
	{
		$hist{$bucket}++;
	} else {
		$hist{$bucket} = 1;
	}
}

foreach $i (sort(keys(%hist)))
{
	print("$i: " . '*'x ($hist{$i}/6) . "\n");
}
